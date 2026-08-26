import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
WORKFLOW_PATH = ROOT / "workflows" / "blender_8way_portrait.json"
API_PATH = ROOT / "workflows" / "blender_8way_portrait_api.json"


def load_workflow():
    return json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))


def load_api_workflow():
    return json.loads(API_PATH.read_text(encoding="utf-8"))


def test_workflow_has_native_model_input_and_two_output_branches():
    workflow = load_workflow()
    types = {node["type"] for node in workflow["nodes"]}
    assert {"NativeModel3DInput", "BlenderEightWayRender", "JoinImageWithAlpha"} <= types
    assert {"Checkpoint Loader (LoraManager)", "Lora Loader (LoraManager)", "Prompt (LoraManager)"} <= types
    assert sum(node["type"] == "SaveImage" for node in workflow["nodes"]) == 2


def test_blender_branch_has_no_prompt_dependency():
    workflow = load_workflow()
    nodes = {node["id"]: node for node in workflow["nodes"]}
    incoming = {}
    for _, source, _, target, _, _ in workflow["links"]:
        incoming.setdefault(target, set()).add(source)

    ancestors = set()
    pending = [3]
    while pending:
        node_id = pending.pop()
        for source in incoming.get(node_id, ()):
            if source not in ancestors:
                ancestors.add(source)
                pending.append(source)

    assert nodes[9]["type"] == "Prompt (LoraManager)"
    assert 9 not in ancestors
    assert nodes[2]["type"] == "NativeModel3DInput"
    assert 2 in ancestors


def test_lora_trigger_words_feed_the_portrait_prompt():
    workflow = load_workflow()
    assert [9, 8, 2, 9, 1, "STRING"] in workflow["links"]


def test_api_workflow_uses_installed_checkpoint_and_expected_defaults():
    prompt = load_api_workflow()
    assert prompt["7"]["inputs"]["ckpt_name"] == "waiIllustriousSDXL_v170.safetensors"
    assert prompt["8"]["class_type"] == "Lora Loader (LoraManager)"
    assert prompt["8"]["inputs"]["loras"] == [
        {
            "name": "pixel-Illustrius.safetensors",
            "strength": 0.45,
            "clipStrength": 0.45,
            "active": True,
        }
    ]
    assert prompt["9"]["class_type"] == "Prompt (LoraManager)"
    assert prompt["3"]["inputs"]["resolution"] == 512
    assert prompt["11"]["inputs"] == {"width": 1024, "height": 1024, "batch_size": 1}


def test_api_workflow_requires_only_model_path_and_portrait_prompt_edits():
    prompt = load_api_workflow()
    assert prompt["2"]["inputs"] == {"model_path": ""}
    assert isinstance(prompt["9"]["inputs"]["text"], str)
    assert "prompt" not in prompt["3"]["inputs"]
