from __future__ import annotations

import json
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

_TRACKER_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "deploys",
    "docker",
    "files",
    "docker-events-track.sh",
)

_STUB = """#!/bin/bash
cmd="$1"; shift
case "$cmd" in
  ps)
    name=""
    refs="$STUB_REFERENCED_VOLUMES"
    while [ $# -gt 0 ]; do
      case "$1" in
        volume=*) name="${1#volume=}" ;;
        network=*) name="${1#network=}"; refs="$STUB_REFERENCED_NETWORKS" ;;
      esac
      shift
    done
    for v in $refs; do
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
      ls)
        filter=""
        while [ $# -gt 0 ]; do
          case "$1" in
            name=*) filter="${1#name=}"; filter="${filter#^}"; filter="${filter%$}" ;;
          esac
          shift
        done
        if [ -n "$STUB_EXISTING_NETWORKS" ]; then
          for n in $STUB_EXISTING_NETWORKS; do
            [ "$n" = "$filter" ] && echo "$n"
          done
        else
          [ -n "$filter" ] && echo "$filter"
        fi
        ;;
      rm)
        echo "$1" >> "$STUB_LOG"
        ;;
    esac
    ;;
  volume)
    sub="$1"; shift
    case "$sub" in
      ls)
        filter=""
        while [ $# -gt 0 ]; do
          case "$1" in
            name=*) filter="${1#name=}"; filter="${filter#^}"; filter="${filter%$}" ;;
          esac
          shift
        done
        if [ -n "$STUB_EXISTING_VOLUMES" ]; then
          for v in $STUB_EXISTING_VOLUMES; do
            [ "$v" = "$filter" ] && echo "$v"
          done
        else
          [ -n "$filter" ] && echo "$filter"
        fi
        ;;
      inspect)
        name="$1"; shift
        fmt=""
        while [ $# -gt 0 ]; do
          if [ "$1" = "--format" ]; then shift; fmt="$1"; fi
          shift
        done
        safe_name=$(echo "$name" | tr '/' '-' | tr ':' '_' | tr '-' '_')
        if echo "$fmt" | grep -q "com.docker.compose.project"; then
          for v in $STUB_COMPOSE_VOLUMES; do
            [ "$v" = "$name" ] && echo "compose-project"
          done
        elif echo "$fmt" | grep -q '{{json .Labels}}'; then
          labels_var="STUB_VOLUME_LABELS_${safe_name}"
          echo "${!labels_var:-{}}"
        elif echo "$fmt" | grep -q '{{json .Options}}'; then
          options_var="STUB_VOLUME_OPTIONS_${safe_name}"
          echo "${!options_var:-{}}"
        fi
        ;;
      rm)
        echo "$1" >> "$STUB_LOG"
        ;;
    esac
    ;;
  inspect)
    cid="$1"; shift
    fmt=""
    while [ $# -gt 0 ]; do
      if [ "$1" = "--format" ]; then shift; fmt="$1"; fi
      shift
    done
    safe_cid=$(echo "$cid" | tr '-' '_')
    if echo "$fmt" | grep -q "Mounts"; then
      vols_var="STUB_CONTAINER_VOLUMES_${safe_cid}"
      echo "${!vols_var:-}"
    elif echo "$fmt" | grep -q "NetworkSettings.Networks"; then
      nets_var="STUB_CONTAINER_NETWORKS_${safe_cid}"
      echo "${!nets_var:-}"
    fi
    ;;
esac
"""

_GETENT_STUB = """#!/bin/bash
if [ "$1" = "passwd" ] && [ "$2" = "${GETENT_HOME_USER:-}" ]; then
  echo "${GETENT_HOME_USER}:x:1000:1000::${GETENT_HOME_DIR}:/bin/bash"
fi
"""

_DATE_STUB = """#!/bin/bash
if [ -n "${STUB_DATE_EPOCH:-}" ]; then
  echo "$STUB_DATE_EPOCH"
else
  exec /usr/bin/date "$@"
fi
"""


def _write_metadata(base: Path, kind: str, name: str, last_used: int) -> None:
    if kind == "volume":
        metadata_dir = base / ".local/share/docker-volume-usage"
    else:
        metadata_dir = base / ".local/share/docker-network-usage"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    safe_name = name.replace("/", "-").replace(":", "_")
    (metadata_dir / f"{safe_name}.json").write_text(f'{{"kind": "{kind}", "name": "{name}", "last_used": {last_used}}}')


def _make_stub_dir(tmp_path: Path) -> Path:
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    (stub_dir / "docker").write_text(_STUB)
    (stub_dir / "docker").chmod(0o755)
    (stub_dir / "getent").write_text(_GETENT_STUB)
    (stub_dir / "getent").chmod(0o755)
    (stub_dir / "date").write_text(_DATE_STUB)
    (stub_dir / "date").chmod(0o755)
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
        "STUB_COMPOSE_VOLUMES": "",
        "STUB_EXISTING_VOLUMES": "",
        "STUB_EXISTING_NETWORKS": "",
        "STUB_LOG": os.path.join(tmp, "rm.log"),
        "CLEANUP_HOME": "",
        "CLEANUP_USER": "",
        "SUDO_USER": "",
    }
    if extra_env:
        env.update(extra_env)
    return subprocess.run(["bash", _SCRIPT], env=env, capture_output=True, text=True)


def _rm_log_text(tmp: Path) -> str:
    rm_log = tmp / "rm.log"
    return rm_log.read_text() if rm_log.exists() else ""


def _run_tracker(
    tmp_path: Path,
    events_file: Path,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    stub_dir = _make_stub_dir(tmp_path)
    env = {
        "HOME": str(tmp_path),
        "PATH": f"{stub_dir}:{os.environ['PATH']}",
        "DOCKER_EVENTS_TRACKER_INPUT": str(events_file),
    }
    if extra_env:
        env.update(extra_env)
    return subprocess.run(["bash", _TRACKER_SCRIPT], env=env, capture_output=True, text=True)


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


def test_cleanup_anonymous_volumes_are_skipped(tmp_path: Path) -> None:
    now = int(time.time())
    stale = now - 61 * 86400
    anon = "a" * 64
    _write_metadata(tmp_path, "volume", anon, stale)
    stub_dir = _make_stub_dir(tmp_path)

    dry = _run_cleanup(str(tmp_path), "true", stub_dir)
    assert dry.returncode == 0, dry.stderr
    assert (tmp_path / ".local/share/docker-volume-usage" / f"{anon}.json").exists()
    assert f"[SKIP] {anon}" in _strip_ansi(dry.stdout)

    result = _run_cleanup(str(tmp_path), "false", stub_dir)
    assert result.returncode == 0, result.stderr
    stdout = _strip_ansi(result.stdout)
    assert not (tmp_path / ".local/share/docker-volume-usage" / f"{anon}.json").exists()
    assert f"[SKIP] {anon}" in stdout
    assert "anonymous volume" in stdout
    assert not (tmp_path / "rm.log").exists()


def test_cleanup_local_path_and_k8s_volumes_are_skipped(tmp_path: Path) -> None:
    now = int(time.time())
    stale = now - 61 * 86400
    volumes = [
        ("pvc-123", {"STUB_VOLUME_LABELS_pvc_123": '{"kubernetes.io/created-for-pvc/name":"my-pvc"}'}),
        ("csi-vol", {"STUB_VOLUME_OPTIONS_csi_vol": '{"csi.storage.k8s.io/pvc/name":"app"}'}),
        ("k8s-vol", {"STUB_VOLUME_LABELS_k8s_vol": '{"something.k8s.io/managed":"true"}'}),
    ]
    for name, _ in volumes:
        _write_metadata(tmp_path, "volume", name, stale)
    stub_dir = _make_stub_dir(tmp_path)
    vol_dir = tmp_path / ".local/share/docker-volume-usage"
    extra_env: dict[str, str] = {}
    for _, env in volumes:
        extra_env.update(env)

    dry = _run_cleanup(str(tmp_path), "true", stub_dir, extra_env)
    assert dry.returncode == 0, dry.stderr
    for name, _ in volumes:
        assert (vol_dir / f"{name}.json").exists()

    result = _run_cleanup(str(tmp_path), "false", stub_dir, extra_env)
    assert result.returncode == 0, result.stderr
    stdout = _strip_ansi(result.stdout)
    assert "externally-provisioned volume" in stdout
    assert not (tmp_path / "rm.log").exists()
    for name, _ in volumes:
        assert not (vol_dir / f"{name}.json").exists()
        assert f"[SKIP] {name}" in stdout


def test_cleanup_compose_volumes_are_skipped(tmp_path: Path) -> None:
    now = int(time.time())
    stale = now - 61 * 86400
    vol_name = "compose-vol"
    _write_metadata(tmp_path, "volume", vol_name, stale)
    stub_dir = _make_stub_dir(tmp_path)
    vol_dir = tmp_path / ".local/share/docker-volume-usage"
    extra_env = {"STUB_COMPOSE_VOLUMES": vol_name}

    dry = _run_cleanup(str(tmp_path), "true", stub_dir, extra_env)
    assert dry.returncode == 0, dry.stderr
    assert (vol_dir / f"{vol_name}.json").exists()
    assert f"[SKIP] {vol_name}" in _strip_ansi(dry.stdout)

    result = _run_cleanup(str(tmp_path), "false", stub_dir, extra_env)
    assert result.returncode == 0, result.stderr
    stdout = _strip_ansi(result.stdout)
    assert not (vol_dir / f"{vol_name}.json").exists()
    assert f"[SKIP] {vol_name}" in stdout
    assert "docker-compose volume" in stdout
    assert not (tmp_path / "rm.log").exists()


def test_cleanup_compose_networks_are_skipped(tmp_path: Path) -> None:
    now = int(time.time())
    stale = now - 61 * 86400
    net_name = "compose-net"
    _write_metadata(tmp_path, "network", net_name, stale)
    stub_dir = _make_stub_dir(tmp_path)
    net_dir = tmp_path / ".local/share/docker-network-usage"
    extra_env = {"STUB_COMPOSE_NETWORKS": net_name}

    dry = _run_cleanup(str(tmp_path), "true", stub_dir, extra_env)
    assert dry.returncode == 0, dry.stderr
    assert (net_dir / f"{net_name}.json").exists()
    assert f"[SKIP] {net_name}" in _strip_ansi(dry.stdout)

    result = _run_cleanup(str(tmp_path), "false", stub_dir, extra_env)
    assert result.returncode == 0, result.stderr
    stdout = _strip_ansi(result.stdout)
    assert not (net_dir / f"{net_name}.json").exists()
    assert f"[SKIP] {net_name}" in stdout
    assert "docker-compose network" in stdout
    assert not (tmp_path / "rm.log").exists()


def test_cleanup_keeps_network_attached_to_stopped_container(tmp_path: Path) -> None:
    now = int(time.time())
    stale = now - 61 * 86400
    _write_metadata(tmp_path, "network", "ref-net", stale)
    stub_dir = _make_stub_dir(tmp_path)

    result = _run_cleanup(str(tmp_path), "false", stub_dir)
    assert result.returncode == 0, result.stderr

    net_dir = tmp_path / ".local/share/docker-network-usage"
    assert (net_dir / "ref-net.json").exists()
    assert "container-ref-net" in _strip_ansi(result.stdout)
    assert not (tmp_path / "rm.log").exists()


def test_cleanup_removes_metadata_for_vanished_volume(tmp_path: Path) -> None:
    now = int(time.time())
    stale = now - 61 * 86400
    _write_metadata(tmp_path, "volume", "vanished-vol", stale)
    stub_dir = _make_stub_dir(tmp_path)
    extra_env = {"STUB_EXISTING_VOLUMES": "other-vol"}

    result = _run_cleanup(str(tmp_path), "false", stub_dir, extra_env)
    assert result.returncode == 0, result.stderr

    vol_dir = tmp_path / ".local/share/docker-volume-usage"
    assert not (vol_dir / "vanished-vol.json").exists()
    stdout = _strip_ansi(result.stdout)
    assert "[SKIP] vanished-vol" in stdout
    assert "(no longer exists)" in stdout
    assert "vanished-vol" not in _rm_log_text(tmp_path)


def test_cleanup_removes_metadata_for_vanished_network(tmp_path: Path) -> None:
    now = int(time.time())
    stale = now - 61 * 86400
    _write_metadata(tmp_path, "network", "vanished-net", stale)
    stub_dir = _make_stub_dir(tmp_path)
    extra_env = {"STUB_EXISTING_NETWORKS": "other-net"}

    result = _run_cleanup(str(tmp_path), "false", stub_dir, extra_env)
    assert result.returncode == 0, result.stderr

    net_dir = tmp_path / ".local/share/docker-network-usage"
    assert not (net_dir / "vanished-net.json").exists()
    stdout = _strip_ansi(result.stdout)
    assert "[SKIP] vanished-net" in stdout
    assert "(no longer exists)" in stdout
    assert "vanished-net" not in _rm_log_text(tmp_path)


def test_cleanup_dry_run_keeps_metadata_for_vanished_resource(tmp_path: Path) -> None:
    now = int(time.time())
    stale = now - 61 * 86400
    _write_metadata(tmp_path, "volume", "vanished-vol", stale)
    _write_metadata(tmp_path, "network", "vanished-net", stale)
    stub_dir = _make_stub_dir(tmp_path)
    extra_env = {"STUB_EXISTING_VOLUMES": "other-vol", "STUB_EXISTING_NETWORKS": "other-net"}

    result = _run_cleanup(str(tmp_path), "true", stub_dir, extra_env)
    assert result.returncode == 0, result.stderr

    assert (tmp_path / ".local/share/docker-volume-usage/vanished-vol.json").exists()
    assert (tmp_path / ".local/share/docker-network-usage/vanished-net.json").exists()
    assert "(no longer exists)" in _strip_ansi(result.stdout)
    assert not (tmp_path / "rm.log").exists()


def test_cleanup_non_numeric_last_used_is_kept(tmp_path: Path) -> None:
    vol_dir = tmp_path / ".local/share/docker-volume-usage"
    vol_dir.mkdir(parents=True)
    (vol_dir / "bad-vol.json").write_text('{"kind": "volume", "name": "bad-vol", "last_used": "not-a-number"}')
    net_dir = tmp_path / ".local/share/docker-network-usage"
    net_dir.mkdir(parents=True)
    (net_dir / "bad-net.json").write_text('{"kind": "network", "name": "bad-net", "last_used": "not-a-number"}')
    stub_dir = _make_stub_dir(tmp_path)

    result = _run_cleanup(str(tmp_path), "false", stub_dir)
    assert result.returncode == 0, result.stderr

    assert (vol_dir / "bad-vol.json").exists()
    assert (net_dir / "bad-net.json").exists()
    stdout = _strip_ansi(result.stdout)
    assert "[KEEP] bad-vol" in stdout and "non-numeric timestamp" in stdout
    assert "[KEEP] bad-net" in stdout and "non-numeric timestamp" in stdout
    assert not (tmp_path / "rm.log").exists()


def test_cleanup_non_numeric_age_threshold_falls_back_to_default(tmp_path: Path) -> None:
    now = int(time.time())
    stale = now - 61 * 86400
    _write_metadata(tmp_path, "volume", "stale-vol", stale)
    _write_metadata(tmp_path, "network", "stale-net", stale)
    stub_dir = _make_stub_dir(tmp_path)
    extra_env = {"AGE_THRESHOLD_DAYS": "abc"}

    result = _run_cleanup(str(tmp_path), "false", stub_dir, extra_env)
    assert result.returncode == 0, result.stderr

    assert not (tmp_path / ".local/share/docker-volume-usage/stale-vol.json").exists()
    assert not (tmp_path / ".local/share/docker-network-usage/stale-net.json").exists()
    rm_log = (tmp_path / "rm.log").read_text()
    assert "stale-vol" in rm_log and "stale-net" in rm_log


def test_cleanup_tolerates_corrupt_metadata(tmp_path: Path) -> None:
    vol_dir = tmp_path / ".local/share/docker-volume-usage"
    vol_dir.mkdir(parents=True)
    (vol_dir / "corrupt-vol.json").write_text("not json")
    net_dir = tmp_path / ".local/share/docker-network-usage"
    net_dir.mkdir(parents=True)
    (net_dir / "corrupt-net.json").write_text("not json")
    stub_dir = _make_stub_dir(tmp_path)

    result = _run_cleanup(str(tmp_path), "false", stub_dir)
    assert result.returncode == 0, result.stderr

    assert (vol_dir / "corrupt-vol.json").exists()
    assert (net_dir / "corrupt-net.json").exists()
    assert not (tmp_path / "rm.log").exists()


def test_tracker_volume_create_writes_metadata(tmp_path: Path) -> None:
    events_file = tmp_path / "events.jsonl"
    events_file.write_text('{"Type":"volume","Action":"create","Actor":{"ID":"my-vol","Attributes":{}}}\n')
    result = _run_tracker(tmp_path, events_file, {"STUB_DATE_EPOCH": "1234567890"})
    assert result.returncode == 0, result.stderr

    metadata = tmp_path / ".local/share/docker-volume-usage/my-vol.json"
    assert metadata.exists()
    data = json.loads(metadata.read_text())
    assert data["name"] == "my-vol"
    assert data["last_used"] == 1234567890


def test_tracker_volume_mount_refreshes_last_used(tmp_path: Path) -> None:
    metadata = tmp_path / ".local/share/docker-volume-usage/my-vol.json"
    metadata.parent.mkdir(parents=True)
    metadata.write_text('{"kind":"volume","name":"my-vol","last_used":1000}')
    events_file = tmp_path / "events.jsonl"
    events_file.write_text('{"Type":"volume","Action":"mount","Actor":{"ID":"my-vol","Attributes":{}}}\n')
    result = _run_tracker(tmp_path, events_file, {"STUB_DATE_EPOCH": "1234567890"})
    assert result.returncode == 0, result.stderr

    data = json.loads(metadata.read_text())
    assert data["last_used"] == 1234567890


def test_tracker_container_start_refreshes_volumes_and_networks(tmp_path: Path) -> None:
    events_file = tmp_path / "events.jsonl"
    events_file.write_text(
        '{"Type":"container","Action":"start","Actor":{"ID":"abc123","Attributes":{"image":"my-image"}}}\n'
    )
    result = _run_tracker(
        tmp_path,
        events_file,
        {
            "STUB_DATE_EPOCH": "1234567890",
            "STUB_CONTAINER_VOLUMES_abc123": "vol-a vol-b",
            "STUB_CONTAINER_NETWORKS_abc123": "net-a net-b",
        },
    )
    assert result.returncode == 0, result.stderr

    for name in ["vol-a", "vol-b"]:
        metadata = tmp_path / f".local/share/docker-volume-usage/{name}.json"
        assert metadata.exists(), name
        data = json.loads(metadata.read_text())
        assert data["name"] == name
        assert data["last_used"] == 1234567890
    for name in ["net-a", "net-b"]:
        metadata = tmp_path / f".local/share/docker-network-usage/{name}.json"
        assert metadata.exists(), name
        data = json.loads(metadata.read_text())
        assert data["name"] == name
        assert data["last_used"] == 1234567890
    image_metadata = tmp_path / ".local/share/docker-image-usage/my-image.json"
    assert image_metadata.exists()
    data = json.loads(image_metadata.read_text())
    assert data["name"] == "my-image"
    assert data["last_used"] == 1234567890


def test_tracker_destroy_deletes_metadata(tmp_path: Path) -> None:
    metadata = tmp_path / ".local/share/docker-volume-usage/my-vol.json"
    metadata.parent.mkdir(parents=True)
    metadata.write_text('{"kind":"volume","name":"my-vol","last_used":1000}')
    events_file = tmp_path / "events.jsonl"
    events_file.write_text('{"Type":"volume","Action":"destroy","Actor":{"ID":"my-vol","Attributes":{}}}\n')
    result = _run_tracker(tmp_path, events_file)
    assert result.returncode == 0, result.stderr

    assert not metadata.exists()


def test_tracker_older_event_does_not_overwrite_newer_last_used(tmp_path: Path) -> None:
    metadata = tmp_path / ".local/share/docker-volume-usage/my-vol.json"
    metadata.parent.mkdir(parents=True)
    metadata.write_text('{"kind":"volume","name":"my-vol","last_used":2000}')
    events_file = tmp_path / "events.jsonl"
    events_file.write_text('{"Type":"volume","Action":"mount","Actor":{"ID":"my-vol","Attributes":{}}}\n')
    result = _run_tracker(tmp_path, events_file, {"STUB_DATE_EPOCH": "1000"})
    assert result.returncode == 0, result.stderr

    data = json.loads(metadata.read_text())
    assert data["last_used"] == 2000


def test_tracker_image_pull_and_container_start_image_tracking(tmp_path: Path) -> None:
    events_file = tmp_path / "events.jsonl"
    events_file.write_text(
        '{"Type":"image","Action":"pull","Actor":{"Attributes":{"name":"pulled-image"}}}\n'
        '{"Type":"container","Action":"start","Actor":{"ID":"abc123","Attributes":{"image":"started-image"}}}\n'
    )
    result = _run_tracker(tmp_path, events_file, {"STUB_DATE_EPOCH": "1234567890"})
    assert result.returncode == 0, result.stderr

    pulled = tmp_path / ".local/share/docker-image-usage/pulled-image.json"
    started = tmp_path / ".local/share/docker-image-usage/started-image.json"
    assert pulled.exists()
    assert started.exists()
    assert json.loads(pulled.read_text())["last_used"] == 1234567890
    assert json.loads(started.read_text())["last_used"] == 1234567890
