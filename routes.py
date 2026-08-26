"""Local-only ComfyUI routes for the native Windows model picker."""

from __future__ import annotations

import asyncio
import os

from aiohttp import web
from server import PromptServer

from .windows_dialog import pick_model_file


def is_local_request(request) -> bool:
    return getattr(request, "remote", None) in (
        None,
        "127.0.0.1",
        "::1",
        "::ffff:127.0.0.1",
    )


@PromptServer.instance.routes.post("/blender-8way/pick-model")
async def pick_model_route(request):
    if not is_local_request(request):
        return web.json_response(
            {"error": "The native dialog can only be opened from the ComfyUI host."},
            status=403,
        )
    if os.name != "nt":
        return web.json_response({"supported": False}, status=501)

    payload = await request.json() if request.can_read_body else {}
    try:
        selected = await asyncio.to_thread(pick_model_file, payload.get("initial_path"))
    except (OSError, ValueError) as error:
        return web.json_response({"error": str(error)}, status=500)
    return web.json_response(
        {"supported": True, "cancelled": selected is None, "path": selected}
    )
