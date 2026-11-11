import pytest
import yaml
from pathlib import Path
from zoe.settings import load_project_config
from zoe.utils.errors import ConfigError


@pytest.mark.automated
def test_config_rejects_unknown_field(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Point working directory or config path to test fixture
    projects_dir = tmp_path / "config" / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

    invalid_config = {
        "project": {
            "id": "invalid_proj",
            "name": "Invalid Project",
        },
        "unexpected_top_level_field": "disallowed_value",
    }

    config_file = projects_dir / "invalid_proj.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(invalid_config, f)

    monkeypatch.chdir(tmp_path)

    with pytest.raises(ConfigError) as exc_info:
        load_project_config("invalid_proj")

    assert "Unknown top-level field" in str(exc_info.value)

