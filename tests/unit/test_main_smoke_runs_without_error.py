import pytest
from pathlib import Path
from zoe.main import main


@pytest.mark.automated
def test_main_smoke_runs_without_error() -> None:
    # Ensure main smoke run completes cleanly with exit code 0
    exit_code = main(project_id="example_project")
    assert exit_code == 0

    # Ensure operational.db was created and has tables
    op_db_path = Path("data/operational/operational.db")
    assert op_db_path.exists()

