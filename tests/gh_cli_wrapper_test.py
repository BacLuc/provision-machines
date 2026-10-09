import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[1] / "deploys/development_tools/ai_agent_devcontainer/files/gh-cli-wrapper.py"
SPEC = importlib.util.spec_from_file_location("gh_cli_wrapper", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise AssertionError("could not load gh cli wrapper")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@pytest.mark.parametrize(
    "endpoint",
    ["user/repos", "orgs/bac-luc/repos", "search/issues"],
)
def test_rest_mutations_without_owned_repo_are_denied(endpoint: str) -> None:
    with pytest.raises(ValueError, match="owned repos/OWNER/REPO"):
        MODULE.validate_api([endpoint, "-X", "POST"])


def test_rest_mutation_requires_owned_repo() -> None:
    with pytest.raises(ValueError):
        MODULE.validate_api(["repos/ecamp/ecamp3/issues", "-X", "POST"])
    MODULE.validate_api(["repos/bacluc-agent/ecamp3/issues", "-X", "POST"])
