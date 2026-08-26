"""Launch Blender and load its eight rendered PNGs into ComfyUI tensors."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

try:
    from .model_files import resolve_model_path
except ImportError:  # Direct module import in lightweight test environments.
    from model_files import resolve_model_path


DIRECTION_NAMES = ("s", "sw", "w", "nw", "n", "ne", "e", "se")


def find_blender_executable() -> Path:
    configured = os.environ.get("BLENDER_EXECUTABLE")
    candidates = [
        configured,
        shutil.which("blender"),
        r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe",
        r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate).resolve()
    raise FileNotFoundError(
        "Blender was not found. Install Blender or set BLENDER_EXECUTABLE to blender.exe."
    )


def render_key(model_path: Path, resolution: int) -> str:
    stat = model_path.stat()
    fingerprint = f"{model_path}|{stat.st_mtime_ns}|{stat.st_size}|{resolution}"
    return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:10]


def build_blender_command(
    blender_executable: Path,
    script_path: Path,
    model_path: Path,
    output_directory: Path,
    resolution: int,
) -> list[str]:
    return [
        str(blender_executable),
        "--background",
        "--factory-startup",
        "--python",
        str(script_path),
        "--",
        "--model",
        str(model_path),
        "--output",
        str(output_directory),
        "--resolution",
        str(resolution),
    ]


def run_blender_render(model_value: str, output_root: Path, resolution: int) -> Path:
    model_path = resolve_model_path(model_value)
    script_path = Path(__file__).parent / "blender_scripts" / "render_8way.py"
    output_directory = output_root / f"{model_path.stem}_{render_key(model_path, resolution)}"
    output_directory.mkdir(parents=True, exist_ok=True)

    command = build_blender_command(
        find_blender_executable(), script_path, model_path, output_directory, resolution
    )
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
        check=False,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    if completed.returncode:
        details = (completed.stderr or completed.stdout)[-4000:]
        raise RuntimeError(f"Blender 8-way render failed (exit {completed.returncode}):\n{details}")

    missing = [
        f"{index:02d}_{name}.png"
        for index, name in enumerate(DIRECTION_NAMES)
        if not (output_directory / f"{index:02d}_{name}.png").is_file()
    ]
    if missing:
        raise RuntimeError(f"Blender completed without all eight renders: {', '.join(missing)}")
    return output_directory


def load_render_batch(output_directory: Path):
    import numpy as np
    import torch
    from PIL import Image

    images = []
    masks = []
    for index, name in enumerate(DIRECTION_NAMES):
        image_path = output_directory / f"{index:02d}_{name}.png"
        with Image.open(image_path) as image:
            rgba = np.asarray(image.convert("RGBA"), dtype=np.float32) / 255.0
        images.append(torch.from_numpy(rgba[:, :, :3]))
        masks.append(torch.from_numpy(1.0 - rgba[:, :, 3]))
    return torch.stack(images), torch.stack(masks)
