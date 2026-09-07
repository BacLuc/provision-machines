import os
import subprocess
import time
from pathlib import Path

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


def _run_cleanup(tmp: str, dry_run: str, stub_dir: str) -> subprocess.CompletedProcess[str]:
    env = {
        "HOME": tmp,
        "DRY_RUN": dry_run,
        "PATH": f"{stub_dir}:{os.environ['PATH']}",
        "STUB_REFERENCED_VOLUMES": "ref-vol",
        "STUB_REFERENCED_NETWORKS": "ref-net",
        "STUB_COMPOSE_NETWORKS": "",
        "STUB_LOG": os.path.join(tmp, "rm.log"),
    }
    return subprocess.run(["bash", _SCRIPT], env=env, capture_output=True, text=True)


def test_cleanup_deletes_only_tracked_idle_unreferenced(tmp_path: Path) -> None:
    now = int(time.time())
    stale = now - 61 * 86400
    fresh = now - 1 * 86400
    vol_dir = tmp_path / ".local/share/docker-volume-usage"
    net_dir = tmp_path / ".local/share/docker-network-usage"
    vol_dir.mkdir(parents=True)
    net_dir.mkdir(parents=True)
    for name, ts in [("stale-vol", stale), ("fresh-vol", fresh), ("ref-vol", stale)]:
        (vol_dir / f"{name}.json").write_text(f'{{"kind": "volume", "name": "{name}", "last_used": {ts}}}')
    for name, ts in [("stale-net", stale), ("fresh-net", fresh), ("ref-net", stale)]:
        (net_dir / f"{name}.json").write_text(f'{{"kind": "network", "name": "{name}", "last_used": {ts}}}')

    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    (stub_dir / "docker").write_text(_STUB)
    (stub_dir / "docker").chmod(0o755)

    result = _run_cleanup(str(tmp_path), "false", str(stub_dir))
    assert result.returncode == 0, result.stderr

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


def test_cleanup_dry_run_removes_nothing(tmp_path: Path) -> None:
    now = int(time.time())
    stale = now - 61 * 86400
    vol_dir = tmp_path / ".local/share/docker-volume-usage"
    net_dir = tmp_path / ".local/share/docker-network-usage"
    vol_dir.mkdir(parents=True)
    net_dir.mkdir(parents=True)
    (vol_dir / "stale-vol.json").write_text(f'{{"kind": "volume", "name": "stale-vol", "last_used": {stale}}}')
    (net_dir / "stale-net.json").write_text(f'{{"kind": "network", "name": "stale-net", "last_used": {stale}}}')

    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    (stub_dir / "docker").write_text(_STUB)
    (stub_dir / "docker").chmod(0o755)

    result = _run_cleanup(str(tmp_path), "true", str(stub_dir))
    assert result.returncode == 0, result.stderr

    assert (vol_dir / "stale-vol.json").exists()
    assert (net_dir / "stale-net.json").exists()
    assert not (tmp_path / "rm.log").exists()
