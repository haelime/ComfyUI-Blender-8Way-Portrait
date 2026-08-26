import ast
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_installer_targets_desktop_custom_nodes_and_workflows():
    installer = (ROOT / "scripts" / "install_windows.ps1").read_text(encoding="utf-8")
    assert "Comfy-Desktop\\ComfyUI-Installs\\ComfyUI\\ComfyUI" in installer
    assert "New-Item -ItemType Junction" in installer
    assert "blender_8way_portrait.json" in installer
    assert "Remove-Item" not in installer


def test_live_verifier_is_valid_python_and_requires_both_outputs():
    source = (ROOT / "scripts" / "verify_workflow.py").read_text(encoding="utf-8")
    ast.parse(source)
    assert "len(render_images) != 8" in source
    assert "len(portrait_images) != 1" in source
