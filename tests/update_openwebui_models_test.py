import importlib.util
import os
from pathlib import Path

import pytest

_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts",
    "update-openwebui-models.py",
)
_spec = importlib.util.spec_from_file_location("update_openwebui_models", _SCRIPT)
assert _spec is not None
assert _spec.loader is not None
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

_RESOURCES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "deploys",
    "openwebui",
    "files",
    "aisix-resources.yaml",
)

MODEL_MAP = {
    "chat": "router-chat",
    "chat_thinking": "router-chat-thinking",
    "web_research": "router-web-research",
    "translate_de": "router-translate-de",
    "translate_en": "router-translate-en",
    "fix_grammar_en": "router-fix-grammar-en",
    "fix_grammar_de": "router-fix-grammar-de",
    "linux_cli": "router-linux-cli",
}
DEFAULT_MODELS = [
    "chat",
    "chat_thinking",
    "web_research",
    "translate_de",
    "translate_en",
    "fix_grammar_en",
    "fix_grammar_de",
    "linux_cli",
]
EXPECTED_NAMES = {
    "chat": "Chat",
    "chat_thinking": "Chat (Thinking)",
    "web_research": "Web Research",
    "translate_de": "Translate to German",
    "translate_en": "Translate to English",
    "fix_grammar_en": "Fix English Grammar",
    "fix_grammar_de": "Fix German Grammar",
    "linux_cli": "Linux CLI",
}


def test_build_preset_specs_all_eight() -> None:
    specs = mod.build_preset_specs(MODEL_MAP, DEFAULT_MODELS)
    assert [s["id"] for s in specs] == DEFAULT_MODELS
    for spec in specs:
        assert spec["base_model_id"] == MODEL_MAP[spec["id"]]
        assert spec["name"] == EXPECTED_NAMES[spec["id"]]
        assert spec["id"] != spec["base_model_id"]


def test_build_preset_specs_rejects_id_collision() -> None:
    bad_map = dict(MODEL_MAP)
    bad_map["chat"] = "chat"
    with pytest.raises(ValueError):
        mod.build_preset_specs(bad_map, DEFAULT_MODELS)


def test_build_preset_specs_rejects_unknown_preset() -> None:
    with pytest.raises(ValueError):
        mod.build_preset_specs(MODEL_MAP, ["chat", "unknown"])


def test_build_preset_specs_rejects_missing_map_entry() -> None:
    with pytest.raises(ValueError):
        mod.build_preset_specs({"chat": "router-chat"}, DEFAULT_MODELS)


def test_sync_payload_exact_shape() -> None:
    specs = mod.build_preset_specs(MODEL_MAP, DEFAULT_MODELS)
    now = 1790288638
    models = [mod.to_sync_model(spec, "admin", now) for spec in specs]
    payload = {"models": models}
    assert list(payload["models"][0].keys()) == [
        "id",
        "user_id",
        "base_model_id",
        "name",
        "params",
        "meta",
        "access_grants",
        "is_active",
        "updated_at",
        "created_at",
    ]
    assert [m["id"] for m in payload["models"]] == DEFAULT_MODELS
    assert [m["base_model_id"] for m in payload["models"]] == [MODEL_MAP[p] for p in DEFAULT_MODELS]
    assert [m["name"] for m in payload["models"]] == [EXPECTED_NAMES[p] for p in DEFAULT_MODELS]
    for model in payload["models"]:
        assert model["user_id"] == "admin"
        assert model["access_grants"] == []
        assert model["is_active"] is True
        assert model["updated_at"] == now
        assert model["created_at"] == now


def test_web_research_payload() -> None:
    specs = mod.build_preset_specs(MODEL_MAP, DEFAULT_MODELS)
    model = mod.to_sync_model(next(s for s in specs if s["id"] == "web_research"), "admin", 1790288638)
    assert model["params"] == {"function_calling": "native"}
    assert model["meta"] == {
        "capabilities": {"web_search": True},
        "defaultFeatureIds": ["web_search"],
        "builtinTools": {"web_search": True},
    }


def test_non_web_research_payload_empty_params_meta() -> None:
    specs = mod.build_preset_specs(MODEL_MAP, DEFAULT_MODELS)
    for spec in specs:
        if spec["id"] == "web_research":
            continue
        model = mod.to_sync_model(spec, "admin", 1790288638)
        assert model["params"] == {}
        assert model["meta"] == {}


def test_parse_aisix_model_names_returns_eight_aliases() -> None:
    with open(_RESOURCES) as f:
        aliases = mod.parse_aisix_model_names(f.read())
    assert [name for name, _ in aliases] == [
        "router-chat",
        "router-chat-thinking",
        "router-web-research",
        "router-translate-de",
        "router-translate-en",
        "router-fix-grammar-en",
        "router-fix-grammar-de",
        "router-linux-cli",
    ]
    for _, targets in aliases:
        assert targets == ["zen-chat", "ollama-chat"]


def test_parse_aisix_model_names_rejects_tabs() -> None:
    with pytest.raises(ValueError):
        mod.parse_aisix_model_names("models:\n\t- display_name: x\n")


def test_parse_aisix_model_names_rejects_flow_style() -> None:
    with pytest.raises(ValueError):
        mod.parse_aisix_model_names("models: [{display_name: x}]\n")


def test_parse_aisix_model_names_rejects_duplicate_keys() -> None:
    with pytest.raises(ValueError):
        mod.parse_aisix_model_names("models:\n  - display_name: a\n    display_name: b\n")


def test_parse_aisix_model_names_rejects_missing_models() -> None:
    with pytest.raises(ValueError):
        mod.parse_aisix_model_names("api_keys:\n  - display_name: k\n")


def test_read_env_file_parses_values(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("# comment\n\nOPENCODE_API_KEY=sk-test\nOLLAMA_API_KEY=\nOPENWEBUI_CALLER_KEY=caller\n")
    env = mod.read_env_file(str(env_file))
    assert env == {
        "OPENCODE_API_KEY": "sk-test",
        "OLLAMA_API_KEY": "",
        "OPENWEBUI_CALLER_KEY": "caller",
    }


def test_read_env_file_does_not_print_secrets(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("OPENCODE_API_KEY=sk-super-secret\n")
    mod.read_env_file(str(env_file))
    assert capsys.readouterr().out == ""
