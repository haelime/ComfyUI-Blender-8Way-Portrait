"""ComfyUI nodes for selecting and rendering a 3D model."""

from __future__ import annotations

from pathlib import Path

import folder_paths

from .blender_render import DIRECTION_NAMES, load_render_batch, run_blender_render
from .model_files import resolve_model_path


class NativeModel3DInput:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_path": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                        "tooltip": "Use the native picker button or paste an absolute 3D model path.",
                    },
                )
            }
        }

    RETURN_TYPES = ("MODEL_3D_PATH",)
    RETURN_NAMES = ("model_path",)
    FUNCTION = "select"
    CATEGORY = "Blender 8-Way/input"

    @classmethod
    def IS_CHANGED(cls, model_path: str):
        try:
            path = resolve_model_path(model_path)
        except (ValueError, FileNotFoundError):
            return model_path
        stat = path.stat()
        return f"{path}:{stat.st_mtime_ns}:{stat.st_size}"

    def select(self, model_path: str):
        return (str(resolve_model_path(model_path)),)


class BlenderEightWayRender:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_path": ("MODEL_3D_PATH",),
                "resolution": (
                    "INT",
                    {
                        "default": 512,
                        "min": 128,
                        "max": 2048,
                        "step": 64,
                    },
                ),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING")
    RETURN_NAMES = ("renders", "alpha", "render_directory", "directions")
    FUNCTION = "render"
    CATEGORY = "Blender 8-Way/render"

    def render(self, model_path: str, resolution: int):
        output_root = Path(folder_paths.get_output_directory()) / "blender_8way"
        output_directory = run_blender_render(model_path, output_root, resolution)
        images, masks = load_render_batch(output_directory)
        return images, masks, str(output_directory), ",".join(DIRECTION_NAMES)


NODE_CLASS_MAPPINGS = {
    "NativeModel3DInput": NativeModel3DInput,
    "BlenderEightWayRender": BlenderEightWayRender,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NativeModel3DInput": "3D Model Input (Windows IFileOpenDialog)",
    "BlenderEightWayRender": "Blender 8-Way Render",
}
