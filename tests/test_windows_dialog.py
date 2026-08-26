from pathlib import Path

import windows_dialog


def test_filter_uses_only_supported_model_extensions():
    pattern = ";".join(f"*{suffix}" for suffix in windows_dialog.SUPPORTED_MODEL_EXTENSIONS)
    assert "*.glb" in pattern
    assert "*.fbx" in pattern
    assert "*.png" not in pattern


def test_initial_directory_uses_selected_file_parent(tmp_path):
    model = tmp_path / "unit.glb"
    model.write_bytes(b"glTF")
    assert windows_dialog._initial_directory(str(model)) == tmp_path.resolve()


def test_native_implementation_names_ifile_open_dialog():
    source = Path(windows_dialog.__file__).read_text(encoding="utf-8")
    assert "DC1C5A9C-E88A-4DDE-A5A1-60F82A20AEF7" in source
    assert "D57C7288-D4AD-4768-BE02-9D969532D960" in source
    assert "SHBrowseForFolder" not in source
