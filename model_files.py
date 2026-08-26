"""Shared validation for 3D model file inputs."""

from __future__ import annotations

from pathlib import Path


SUPPORTED_MODEL_EXTENSIONS = (
    ".blend",
    ".fbx",
    ".glb",
    ".gltf",
    ".obj",
    ".ply",
    ".stl",
    ".usd",
    ".usda",
    ".usdc",
)


def resolve_model_path(value: str) -> Path:
    if not value or not value.strip():
        raise ValueError("Choose a 3D model file before queuing the workflow.")

    model_path = Path(value).expanduser().resolve()
    if not model_path.is_file():
        raise FileNotFoundError(f"3D model file does not exist: {model_path}")
    if model_path.suffix.lower() not in SUPPORTED_MODEL_EXTENSIONS:
        allowed = ", ".join(SUPPORTED_MODEL_EXTENSIONS)
        raise ValueError(f"Unsupported 3D model format '{model_path.suffix}'. Expected one of: {allowed}")
    return model_path
