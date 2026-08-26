from pathlib import Path

import blender_render


ROOT = Path(__file__).parents[1]


def test_command_uses_argument_list_and_fixed_headless_script():
    command = blender_render.build_blender_command(
        Path("C:/Blender/blender.exe"),
        ROOT / "blender_scripts" / "render_8way.py",
        ROOT / "tests" / "fixtures" / "cube.obj",
        Path("C:/output with spaces"),
        512,
    )
    assert command[:3] == ["C:\\Blender\\blender.exe", "--background", "--factory-startup"]
    assert command[command.index("--resolution") + 1] == "512"
    assert "--python" in command


def test_direction_contract_is_exactly_eight_unique_names():
    assert blender_render.DIRECTION_NAMES == ("s", "sw", "w", "nw", "n", "ne", "e", "se")
    assert len(set(blender_render.DIRECTION_NAMES)) == 8


def test_blender_script_has_no_prompt_input():
    script = (ROOT / "blender_scripts" / "render_8way.py").read_text(encoding="utf-8")
    assert "--model" in script
    assert "--output" in script
    assert "--prompt" not in script
    assert "bpy.ops.render.render(write_still=True)" in script
