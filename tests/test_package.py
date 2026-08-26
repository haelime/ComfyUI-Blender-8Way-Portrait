import ast
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_package_exports_comfyui_entry_points():
    tree = ast.parse((ROOT / "__init__.py").read_text(encoding="utf-8"))
    assigned = {
        target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    assert {"NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"} <= assigned


def test_repository_does_not_track_generated_media_or_models():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "render_output/" in ignore
    assert ".venv/" in ignore
