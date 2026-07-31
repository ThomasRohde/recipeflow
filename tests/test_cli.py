from pathlib import Path

from typer.testing import CliRunner

from recipeflow.cli.main import app

runner = CliRunner()
FIXTURE = Path(__file__).parents[1] / "examples" / "espresso-brownies.recipe.yaml"


def test_validate_cli() -> None:
    result = runner.invoke(app, ["validate", str(FIXTURE), "--json"])
    assert result.exit_code == 0
    assert '"valid": true' in result.stdout


def test_render_cli() -> None:
    result = runner.invoke(app, ["render", str(FIXTURE), "--format", "text"])
    assert result.exit_code == 0
    assert "Espresso Brownies" in result.stdout
