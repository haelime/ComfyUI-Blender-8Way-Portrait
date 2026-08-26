# ComfyUI Blender 8-Way + AI Portrait

3D 모델 파일과 portrait 프롬프트를 한 번 입력해 서로 독립적인 두 결과를 만드는 ComfyUI 워크플로입니다.

- Blender가 45도 간격의 투명 PNG 8장을 렌더합니다.
- 설치된 LoRA Manager와 이미지 생성 모델이 AI 캐릭터 초상화를 만듭니다.

Blender 분기에는 프롬프트 연결이 전혀 없습니다. 방향과 카메라, 조명은 항상 동일합니다.

## 확인된 환경

- Windows 11 / ComfyUI Desktop 0.34.0
- Blender 5.2.1 LTS
- ComfyUI-LoRA-Manager 1.2.0
- `waiIllustriousSDXL_v170.safetensors`
- `pixel-Illustrius.safetensors` (model/CLIP 강도 0.45)

모델 파일은 저장소에 포함되지 않습니다. 다른 PC에서는 워크플로의 LoRA Manager 노드에서 호환되는
checkpoint와 LoRA를 고르면 됩니다.

## 설치

PowerShell에서 저장소 폴더로 이동해 실행합니다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_windows.ps1
```

스크립트는 다음 두 작업만 합니다.

1. 이 저장소를 ComfyUI Desktop의 `custom_nodes/comfyui-blender-8way-portrait`에 Junction으로 연결합니다.
2. `workflows/blender_8way_portrait.json`을 ComfyUI의 `user/default/workflows`에 복사합니다.

그 후 ComfyUI 백엔드를 재시작하고 `blender_8way_portrait` 워크플로를 여세요.

## 사용법

1. **INPUT 1 — 3D MODEL**에서 **Choose 3D Model…** 버튼을 누릅니다.
2. Windows Explorer의 최신 Common Item Dialog에서 모델을 고릅니다.
3. **INPUT 2 — PORTRAIT PROMPT**의 문구를 원하는 캐릭터 설명으로 바꿉니다.
4. Queue를 한 번 실행합니다.

파일 선택은 HTML 업로드가 아니라 Windows `IFileOpenDialog`를 직접 호출합니다. 모델을 ComfyUI input
폴더로 복사하지 않고 원래 절대경로를 Blender에 안전한 인자 배열로 전달합니다. 선택창 API는 로컬호스트
요청만 허용합니다.

지원 형식:

```text
.blend .fbx .glb .gltf .obj .ply .stl .usd .usda .usdc
```

Blender 자동 검색이 실패하면 환경변수 `BLENDER_EXECUTABLE`에 `blender.exe`의 전체 경로를 지정하세요.

## 결과

8방향 순서는 다음과 같습니다.

```text
00_s, 01_sw, 02_w, 03_nw, 04_n, 05_ne, 06_e, 07_se
```

- Blender 원본: `ComfyUI/output/blender_8way/<모델명>_<키>/`
- 워크플로 저장본: `ComfyUI/output/blender_8way/`
- AI 초상화: `ComfyUI/output/portrait/`

렌더러는 모델을 원점과 바닥에 자동 정렬하고, 고정 orthographic 카메라(고도 35도)와 Eevee 조명을
구성합니다. 각 방향은 카메라를 바꾸지 않고 모델 root를 45도씩 돌려 만들기 때문에 프롬프트 및 AI 모델과
무관하게 재현됩니다.

LoRA Manager는 기본으로 `pixel-Illustrius.safetensors`를 0.45 강도로 적용하고, Manager가 반환하는
trigger words를 `Prompt (LoraManager)`에 자동 연결합니다. LoRA를 교체해도 배선은 바꿀 필요가 없습니다.

## 검증

```powershell
uv run --with pytest pytest -q
python scripts/verify_workflow.py tests/fixtures/cube.obj --quick
```

두 번째 명령은 실행 중인 `127.0.0.1:8188`에 전체 API 워크플로를 제출하고, Blender PNG 8장과 AI
portrait 1장이 모두 반환되는지 확인합니다.
