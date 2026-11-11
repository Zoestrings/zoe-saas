import pytest
import yaml
from pathlib import Path
from zoe.settings import load_project_config
from zoe.utils.errors import ConfigError


@pytest.mark.automated
def test_public_config_rejects_secret(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    projects_dir = tmp_path / "config" / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

    secret_config = {
        "project": {
            "id": "secret_proj",
            "name": "Secret Project",
        },
        "telegram": {
            "environment": "pilot",
            "bot_token": "x",
        },
    }

    config_file = projects_dir / "secret_proj.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(secret_config, f)

    monkeypatch.chdir(tmp_path)

    with pytest.raises(ConfigError) as exc_info:
        load_project_config("secret_proj")

    assert "Secret-like key" in str(exc_info.value) or "bot_token" in str(exc_info.value)

