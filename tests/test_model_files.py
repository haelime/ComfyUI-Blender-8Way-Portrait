from pathlib import Path

import pytest

from model_files import SUPPORTED_MODEL_EXTENSIONS, resolve_model_path


ROOT = Path(__file__).parents[1]


def test_supported_formats_cover_common_blender_importers():
    assert {".blend", ".fbx", ".glb", ".gltf", ".obj", ".usd", ".stl", ".ply"} <= set(
        SUPPORTED_MODEL_EXTENSIONS
    )


def test_model_path_must_exist_and_use_a_supported_extension(tmp_path):
    with pytest.raises(FileNotFoundError):
        resolve_model_path(str(tmp_path / "missing.glb"))

    unsupported = tmp_path / "model.txt"
    unsupported.write_text("not a model", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported"):
        resolve_model_path(str(unsupported))


def test_fixture_model_resolves():
    model = resolve_model_path(str(ROOT / "tests" / "fixtures" / "cube.obj"))
    assert model.name == "cube.obj"
