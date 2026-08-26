$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$comfyRoot = Join-Path $env:LOCALAPPDATA "Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI"
$customNodes = Join-Path $comfyRoot "custom_nodes"
$nodeLink = Join-Path $customNodes "comfyui-blender-8way-portrait"
$workflowDirectory = Join-Path $comfyRoot "user\default\workflows"
$workflowSource = Join-Path $repositoryRoot "workflows\blender_8way_portrait.json"
$workflowTarget = Join-Path $workflowDirectory "blender_8way_portrait.json"

if (-not (Test-Path -LiteralPath $comfyRoot -PathType Container)) {
    throw "ComfyUI Desktop was not found at: $comfyRoot"
}

if (Test-Path -LiteralPath $nodeLink) {
    $existing = Get-Item -LiteralPath $nodeLink -Force
    $existingTarget = @($existing.Target) -join ""
    if ($existing.LinkType -ne "Junction" -or $existingTarget -ne $repositoryRoot) {
        throw "A different custom node already exists at: $nodeLink"
    }
} else {
    New-Item -ItemType Junction -Path $nodeLink -Target $repositoryRoot | Out-Null
}

New-Item -ItemType Directory -Path $workflowDirectory -Force | Out-Null
Copy-Item -LiteralPath $workflowSource -Destination $workflowTarget -Force

Write-Host "Installed custom node: $nodeLink"
Write-Host "Installed workflow:    $workflowTarget"
Write-Host "Restart the ComfyUI backend before loading the workflow."
