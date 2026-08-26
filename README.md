# ComfyUI Blender 8-Way + AI Portrait

[한국어 설명](README.ko.md)

One ComfyUI workflow takes a 3D model and a portrait prompt, then produces two independent outputs:

- eight transparent PNG renders from Blender at fixed 45-degree directions;
- one LoRA-assisted AI character portrait.

The Blender branch never receives the text prompt. The portrait branch uses the installed
[ComfyUI-LoRA-Manager](https://github.com/willmiao/ComfyUI-Lora-Manager) loader and prompt nodes.

## Requirements

- Windows 10 or 11 with ComfyUI Desktop
- Blender 4.3 or newer (verified with Blender 5.2.1 LTS)
- ComfyUI-LoRA-Manager
- an SDXL/Illustrious checkpoint
- Pillow (normally already included with ComfyUI)

The bundled workflow is preconfigured for these locally detected files:

- checkpoint: `waiIllustriousSDXL_v170.safetensors`
- LoRA: `pixel-Illustrius.safetensors`, model and CLIP strength `0.45`

Choose compatible replacements in the two LoRA Manager nodes if your filenames differ.

## Install on ComfyUI Desktop

Run from PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_windows.ps1
```

The installer creates a directory junction in the active ComfyUI Desktop `custom_nodes` folder
and copies the ready workflow into `user/default/workflows`. Restart the ComfyUI backend, then
load **blender_8way_portrait** from your workflows.

## Use

1. In **INPUT 1 — 3D MODEL**, click **Choose 3D Model…**. This opens Windows Explorer's modern
   `IFileOpenDialog`; no browser upload or copied model is required.
2. Edit **INPUT 2 — PORTRAIT PROMPT**.
3. Optionally change the selected LoRA in **Lora Loader (LoraManager)**.
4. Queue the workflow once.

Supported model formats are `.blend`, `.fbx`, `.glb`, `.gltf`, `.obj`, `.ply`, `.stl`, `.usd`,
`.usda`, and `.usdc`. Set the `BLENDER_EXECUTABLE` environment variable if Blender is installed
outside the standard Blender Foundation or Steam locations.

## Outputs

The transparent render batch is ordered as:

```text
00_s, 01_sw, 02_w, 03_nw, 04_n, 05_ne, 06_e, 07_se
```

Raw Blender PNGs are written below `output/blender_8way/<model>_<content-key>/`. The workflow also
saves the RGBA batch below `output/blender_8way/` and the AI result below `output/portrait/`.

The renderer uses a fixed orthographic camera at 35-degree elevation, fixed lighting, automatic
centering/framing, a transparent world, and Eevee. It rotates the imported model rather than using
prompt-dependent view synthesis.

## Verify

Unit tests:

```powershell
uv run --with pytest pytest -q
```

Live smoke test against an already running ComfyUI server:

```powershell
python scripts/verify_workflow.py tests/fixtures/cube.obj --quick
```

The live verifier submits the API workflow to `127.0.0.1:8188` and requires both the eight-image
Blender output and portrait output to complete successfully.

## License

MIT
