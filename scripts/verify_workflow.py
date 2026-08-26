"""Submit the bundled workflow to a local ComfyUI server and verify both outputs."""

from __future__ import annotations

import argparse
import json
import time
import uuid
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).parents[1]


def request_json(url: str, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    parser.add_argument("--prompt", default="1girl, solo, pixel art, fantasy knight portrait")
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    model = args.model.expanduser().resolve()
    if not model.is_file():
        parser.error(f"model does not exist: {model}")

    workflow = json.loads(
        (ROOT / "workflows" / "blender_8way_portrait_api.json").read_text(encoding="utf-8")
    )
    workflow["2"]["inputs"]["model_path"] = str(model)
    workflow["9"]["inputs"]["text"] = args.prompt
    if args.quick:
        workflow["3"]["inputs"]["resolution"] = 256
        workflow["11"]["inputs"].update(width=512, height=512)
        workflow["12"]["inputs"]["steps"] = 12

    submitted = request_json(
        f"{args.server}/prompt",
        {"prompt": workflow, "client_id": f"blender-8way-verify-{uuid.uuid4()}"},
    )
    prompt_id = submitted["prompt_id"]
    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        history = request_json(f"{args.server}/history/{prompt_id}")
        if prompt_id in history:
            entry = history[prompt_id]
            if entry["status"]["status_str"] != "success":
                raise RuntimeError(json.dumps(entry["status"], indent=2))
            outputs = entry["outputs"]
            render_images = outputs.get("6", {}).get("images", [])
            portrait_images = outputs.get("15", {}).get("images", [])
            if len(render_images) != 8 or len(portrait_images) != 1:
                raise RuntimeError(
                    f"unexpected outputs: {len(render_images)} renders, "
                    f"{len(portrait_images)} portraits"
                )
            print(json.dumps(outputs, indent=2))
            return
        time.sleep(2)
    raise TimeoutError(f"workflow did not complete within {args.timeout} seconds")


if __name__ == "__main__":
    main()
