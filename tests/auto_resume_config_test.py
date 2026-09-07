import json
import re
from pathlib import Path

OPENCODE_CONFIG = (
    Path(__file__).resolve().parent.parent
    / "deploys"
    / "development_tools"
    / "ai_agent_devcontainer"
    / "files"
    / "opencode"
    / "opencode.jsonc"
)

GRACE_PERIOD_MS = 3000
MAX_STALL_MINUTES = 20


def test_auto_resume_stall_budget() -> None:
    stripped = re.sub(r"^[ \t]*//.*$", "", OPENCODE_CONFIG.read_text(), flags=re.MULTILINE)
    json.loads(stripped)
    retries = re.search(r'"maxRetries":\s*(\d+)', stripped)
    timeout = re.search(r'"chunkTimeoutMs":\s*(\d+)', stripped)
    assert retries is not None
    assert timeout is not None
    max_retries = int(retries.group(1))
    chunk_timeout_ms = int(timeout.group(1))
    assert max_retries <= 3
    assert max_retries * ((chunk_timeout_ms + GRACE_PERIOD_MS) / 1000 / 60) <= MAX_STALL_MINUTES
