import os
import subprocess
import textwrap
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "deploys"
    / "charging_state_monitor"
    / "files"
    / "charging-state-monitor.sh"
)


def _write_counter(path: Path, value: int) -> None:
    path.write_text(str(value))


def _make_exec(path: Path, content: str) -> None:
    path.write_text(textwrap.dedent(content))
    os.chmod(path, 0o755)


def _stubs(tmp_path: Path, counter: Path, notify_log: Path, max_iters: int, scenario: str) -> dict[str, str]:
    env = dict(os.environ)
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    env["COUNTER_FILE"] = str(counter)
    env["BASE"] = "1000"
    env["STEP"] = "30"
    env["MAX_ITERS"] = str(max_iters)
    env["SCENARIO"] = scenario
    env["NOTIFY_LOG"] = str(notify_log)

    _make_exec(
        tmp_path / "date",
        """
        #!/bin/bash
        c=$(cat "$COUNTER_FILE")
        echo $((BASE + c * STEP))
        echo $((c + 1)) > "$COUNTER_FILE"
        """,
    )

    _make_exec(
        tmp_path / "acpi",
        """
        #!/bin/bash
        c=$(cat "$COUNTER_FILE")
        idx=$((c - 1))
        if [ "$SCENARIO" = "A" ]; then
            bad=1
        else
            if [ "$idx" -eq 0 ] || [ "$idx" -ge 3 ]; then
                bad=1
            else
                bad=0
            fi
        fi
        if [ "$1" = "-a" ]; then
            if [ "$bad" -eq 1 ]; then
                echo "Adapter 0: on-line"
            else
                echo "Adapter 0: off-line"
            fi
        elif [ "$1" = "-b" ]; then
            if [ "$bad" -eq 1 ]; then
                echo "Battery 0: Discharging, 75%"
            else
                echo "Battery 0: Charging, 75%"
            fi
        fi
        """,
    )

    _make_exec(
        tmp_path / "notify-send",
        """
        #!/bin/bash
        c=$(cat "$COUNTER_FILE")
        idx=$((c - 1))
        now=$((BASE + idx * STEP))
        echo "now=$now $1 $2" >> "$NOTIFY_LOG"
        """,
    )

    _make_exec(
        tmp_path / "sleep",
        """
        #!/bin/bash
        c=$(cat "$COUNTER_FILE")
        idx=$((c - 1))
        if [ "$idx" -ge "$MAX_ITERS" ]; then
            kill -TERM "$PPID"
        fi
        exit 0
        """,
    )

    return env


def _run_and_collect(tmp_path: Path, max_iters: int, scenario: str) -> set[int]:
    counter = tmp_path / "counter"
    notify_log = tmp_path / "notify.log"
    _write_counter(counter, 0)
    notify_log.write_text("")

    env = _stubs(tmp_path, counter, notify_log, max_iters, scenario)

    try:
        subprocess.run(["bash", str(SCRIPT)], env=env, timeout=20)
    except subprocess.TimeoutExpired:
        pass

    result: set[int] = set()
    for line in notify_log.read_text().splitlines():
        for token in line.split():
            if token.startswith("now="):
                result.add(int(token.split("=", 1)[1]))
                break
    return result


def test_scenario_a_persist_and_cooldown(tmp_path: Path) -> None:
    assert _run_and_collect(tmp_path, max_iters=70, scenario="A") == {1060, 2860}


def test_scenario_b_reset_on_clear(tmp_path: Path) -> None:
    assert _run_and_collect(tmp_path, max_iters=10, scenario="B") == {1150}
