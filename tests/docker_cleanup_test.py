from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return _ANSI.sub("", text)


_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "deploys",
    "docker",
    "files",
    "docker-volume-network-cleanup.sh",
)

_STUB = """#!/bin/bash
cmd="$1"; shift
case "$cmd" in
  ps)
    name=""
    while [ $# -gt 0 ]; do
      case "$1" in
        volume=*) name="${1#volume=}" ;;
      esac
      shift
    done
    for v in $STUB_REFERENCED_VOLUMES; do
      [ "$v" = "$name" ] && echo "container-$name"
    done
    ;;
  network)
    sub="$1"; shift
    case "$sub" in
      inspect)
        name="$1"; shift
        fmt=""
        while [ $# -gt 0 ]; do
          if [ "$1" = "--format" ]; then shift; fmt="$1"; fi
          shift
        done
        if echo "$fmt" | grep -q "com.docker.compose.project"; then
          for n in $STUB_COMPOSE_NETWORKS; do
            [ "$n" = "$name" ] && echo "compose-project"
          done
        else
          for n in $STUB_REFERENCED_NETWORKS; do
            [ "$n" = "$name" ] && echo "container-$name"
          done
        fi
        ;;
      rm)
        echo "$1" >> "$STUB_LOG"
        ;;
    esac
    ;;
  volume)
    sub="$1"; shift
    if [ "$sub" = "rm" ]; then
      echo "$1" >> "$STUB_LOG"
    fi
    ;;
esac
"""

_GETENT_STUB = """#!/bin/bash
if [ "$1" = "passwd" ] && [ "$2" = "${GETENT_HOME_USER:-}" ]; then
  echo "${GETENT_HOME_USER}:x:1000:1000::${GETENT_HOME_DIR}:/bin/bash"
fi
"""


def _write_metadata(base: Path, kind: str, name: str, last_used: int) -> None:
    if kind == "volume":
        metadata_dir = base / ".local/share/docker-volume-usage"
    else:
        metadata_dir = base / ".local/share/docker-network-usage"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    (metadata_dir / f"{name}.json").write_text(f'{{"kind": "{kind}", "name": "{name}", "last_used": {last_used}}}')


def _make_stub_dir(tmp_path: Path) -> Path:
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    (stub_dir / "docker").write_text(_STUB)
    (stub_dir / "docker").chmod(0o755)
    (stub_dir / "getent").write_text(_GETENT_STUB)
    (stub_dir / "getent").chmod(0o755)
    return stub_dir


def _run_cleanup(
    tmp: str,
    dry_run: str,
    stub_dir: Path,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = {
        "HOME": tmp,
        "DRY_RUN": dry_run,
        "PATH": f"{stub_dir}:{os.environ['PATH']}",
        "STUB_REFERENCED_VOLUMES": "ref-vol",
        "STUB_REFERENCED_NETWORKS": "ref-net",
        "STUB_COMPOSE_NETWORKS": "",
        "STUB_LOG": os.path.join(tmp, "rm.log"),
        "CLEANUP_HOME": "",
        "CLEANUP_USER": "",
        "SUDO_USER": "",
    }
    if extra_env:
        env.update(extra_env)
    return subprocess.run(["bash", _SCRIPT], env=env, capture_output=True, text=True)


def test_cleanup_deletes_only_tracked_idle_unreferenced(tmp_path: Path) -> None:
    now = int(time.time())
    stale = now - 61 * 86400
    fresh = now - 1 * 86400
    for name, ts in [("stale-vol", stale), ("fresh-vol", fresh), ("ref-vol", stale)]:
        _write_metadata(tmp_path, "volume", name, ts)
    for name, ts in [("stale-net", stale), ("fresh-net", fresh), ("ref-net", stale)]:
        _write_metadata(tmp_path, "network", name, ts)

    stub_dir = _make_stub_dir(tmp_path)
    result = _run_cleanup(str(tmp_path), "false", stub_dir)
    assert result.returncode == 0, result.stderr

    vol_dir = tmp_path / ".local/share/docker-volume-usage"
    net_dir = tmp_path / ".local/share/docker-network-usage"
    assert not (vol_dir / "stale-vol.json").exists()
    assert not (net_dir / "stale-net.json").exists()
    assert (vol_dir / "fresh-vol.json").exists()
    assert (net_dir / "fresh-net.json").exists()
    assert (vol_dir / "ref-vol.json").exists()
    assert (net_dir / "ref-net.json").exists()

    rm_log = (tmp_path / "rm.log").read_text()
    assert "stale-vol" in rm_log and "stale-net" in rm_log
    assert "fresh-vol" not in rm_log and "fresh-net" not in rm_log
    assert "ref-vol" not in rm_log and "ref-net" not in rm_log
    assert "untracked-vol" not in rm_log and "untracked-net" not in rm_log


def test_cleanup_dry_run_keeps_metadata_and_reports(tmp_path: Path) -> None:
    now = int(time.time())
    stale = now - 61 * 86400
    _write_metadata(tmp_path, "volume", "stale-vol", stale)
    _write_metadata(tmp_path, "network", "stale-net", stale)

    stub_dir = _make_stub_dir(tmp_path)
    result = _run_cleanup(str(tmp_path), "true", stub_dir)
    assert result.returncode == 0, result.stderr

    assert (tmp_path / ".local/share/docker-volume-usage/stale-vol.json").exists()
    assert (tmp_path / ".local/share/docker-network-usage/stale-net.json").exists()
    assert not (tmp_path / "rm.log").exists()
    assert "[DELETE]" in _strip_ansi(result.stdout)


def test_cleanup_age_threshold_override(tmp_path: Path) -> None:
    now = int(time.time())
    old = now - 31 * 86400
    young = now - 29 * 86400
    _write_metadata(tmp_path, "volume", "old-vol", old)
    _write_metadata(tmp_path, "volume", "young-vol", young)
    _write_metadata(tmp_path, "network", "old-net", old)
    _write_metadata(tmp_path, "network", "young-net", young)

    stub_dir = _make_stub_dir(tmp_path)
    result = _run_cleanup(str(tmp_path), "false", stub_dir, {"AGE_THRESHOLD_DAYS": "30"})
    assert result.returncode == 0, result.stderr

    vol_dir = tmp_path / ".local/share/docker-volume-usage"
    net_dir = tmp_path / ".local/share/docker-network-usage"
    assert not (vol_dir / "old-vol.json").exists()
    assert not (net_dir / "old-net.json").exists()
    assert (vol_dir / "young-vol.json").exists()
    assert (net_dir / "young-net.json").exists()

    rm_log = (tmp_path / "rm.log").read_text()
    assert "old-vol" in rm_log and "old-net" in rm_log
    assert "young-vol" not in rm_log and "young-net" not in rm_log


def test_cleanup_builtin_networks_are_skipped_and_cleaned(tmp_path: Path) -> None:
    now = int(time.time())
    stale = now - 61 * 86400
    for name in ["bridge", "host", "none"]:
        _write_metadata(tmp_path, "network", name, stale)

    stub_dir = _make_stub_dir(tmp_path)
    result = _run_cleanup(str(tmp_path), "false", stub_dir)
    assert result.returncode == 0, result.stderr

    net_dir = tmp_path / ".local/share/docker-network-usage"
    stdout = _strip_ansi(result.stdout)
    for name in ["bridge", "host", "none"]:
        assert not (net_dir / f"{name}.json").exists()
        assert f"[SKIP] {name}" in stdout
    assert not (tmp_path / "rm.log").exists()


def test_cleanup_dry_run_keeps_builtin_network_metadata(tmp_path: Path) -> None:
    now = int(time.time())
    stale = now - 61 * 86400
    for name in ["bridge", "host", "none"]:
        _write_metadata(tmp_path, "network", name, stale)

    stub_dir = _make_stub_dir(tmp_path)
    result = _run_cleanup(str(tmp_path), "true", stub_dir)
    assert result.returncode == 0, result.stderr

    net_dir = tmp_path / ".local/share/docker-network-usage"
    for name in ["bridge", "host", "none"]:
        assert (net_dir / f"{name}.json").exists()


def test_cleanup_resolves_home_from_cleanup_home(tmp_path: Path) -> None:
    now = int(time.time())
    stale = now - 61 * 86400
    custom_home = tmp_path / "custom-home"
    _write_metadata(custom_home, "volume", "stale-vol", stale)
    _write_metadata(custom_home, "network", "stale-net", stale)

    stub_dir = _make_stub_dir(tmp_path)
    result = _run_cleanup(str(tmp_path), "false", stub_dir, {"CLEANUP_HOME": str(custom_home)})
    assert result.returncode == 0, result.stderr

    assert not (custom_home / ".local/share/docker-volume-usage/stale-vol.json").exists()
    assert not (custom_home / ".local/share/docker-network-usage/stale-net.json").exists()
    rm_log = (tmp_path / "rm.log").read_text()
    assert "stale-vol" in rm_log and "stale-net" in rm_log


def test_cleanup_resolves_home_from_cleanup_user(tmp_path: Path) -> None:
    now = int(time.time())
    stale = now - 61 * 86400
    user_home = tmp_path / "worker-home"
    _write_metadata(user_home, "volume", "stale-vol", stale)

    stub_dir = _make_stub_dir(tmp_path)
    result = _run_cleanup(
        str(tmp_path),
        "false",
        stub_dir,
        {
            "CLEANUP_USER": "worker",
            "GETENT_HOME_USER": "worker",
            "GETENT_HOME_DIR": str(user_home),
        },
    )
    assert result.returncode == 0, result.stderr

    assert not (user_home / ".local/share/docker-volume-usage/stale-vol.json").exists()
    assert "stale-vol" in (tmp_path / "rm.log").read_text()


def test_cleanup_resolves_home_from_sudo_user(tmp_path: Path) -> None:
    now = int(time.time())
    stale = now - 61 * 86400
    user_home = tmp_path / "sudo-home"
    _write_metadata(user_home, "network", "stale-net", stale)

    stub_dir = _make_stub_dir(tmp_path)
    result = _run_cleanup(
        str(tmp_path),
        "false",
        stub_dir,
        {
            "SUDO_USER": "admin",
            "GETENT_HOME_USER": "admin",
            "GETENT_HOME_DIR": str(user_home),
        },
    )
    assert result.returncode == 0, result.stderr

    assert not (user_home / ".local/share/docker-network-usage/stale-net.json").exists()
    assert "stale-net" in (tmp_path / "rm.log").read_text()


def test_cleanup_resolves_home_from_home_fallback(tmp_path: Path) -> None:
    now = int(time.time())
    stale = now - 61 * 86400
    _write_metadata(tmp_path, "volume", "stale-vol", stale)

    stub_dir = _make_stub_dir(tmp_path)
    result = _run_cleanup(str(tmp_path), "false", stub_dir)
    assert result.returncode == 0, result.stderr

    assert not (tmp_path / ".local/share/docker-volume-usage/stale-vol.json").exists()
    assert "stale-vol" in (tmp_path / "rm.log").read_text()
