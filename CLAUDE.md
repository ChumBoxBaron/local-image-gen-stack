# CLAUDE.md — Local Image-Gen Stack

Context for AI coding sessions. Keep this current when conventions or the build change.

## What this repo is
The **recipe** for running Forge + FLUX.1 [dev] fp8 locally on an RTX 5080. It is
**not** a Forge fork — it holds only config, scripts, and docs. The live Forge
install lives in a separate folder (`Image Gen Stack/` on this machine) which is a
full clone of `lllyasviel/stable-diffusion-webui-forge` and is intentionally not
tracked here.

This is the **image** stack, parallel to and independent of the **text** stack
(Ollama + Open WebUI). They share no components.

## Hardware assumptions
RTX 5080, 16 GB VRAM, **Blackwell / sm_120** · Ryzen 9 9950X3D · 64 GB RAM · Windows 11.

## Non-negotiables / gotchas (don't relearn these)
- **cu128 torch is mandatory.** Blackwell needs PyTorch on CUDA 12.8. Forge's default
  (torch 2.3.1 / cu121) can't see the card. Enforced via `TORCH_COMMAND` in
  `config/webui-user.bat`. Always verify `torch.cuda.is_available()` before downloading models.
- **Python 3.11** (or 3.10). Not 3.12+. The venv must be built with it — pinned via
  `PYTHON=` in `webui-user.bat`.
- **Launch with `run_forge.bat`, not `webui-user.bat` directly.** This machine sets
  `NoDefaultCurrentDirectoryInExePath=1`, which breaks Forge's relative `call webui.bat`.
  The launcher clears it and `cd`s to the repo.
- **Models come from non-gated mirrors.** `black-forest-labs/FLUX.1-dev` and `-schnell`
  are gated now. Use `Kijai/flux-fp8` and `comfyanonymous/flux_text_encoders`.
- **numpy must stay 1.26.x.** numpy 2.x breaks the pinned scikit-image (ABI). If a
  `pip install` bumps it, the UI dies with `numpy.dtype size changed` — downgrade back.
- **FLUX guidance:** real CFG = 1, distilled CFG ≈ 3.5. Don't treat it like SDXL.

## Conventions
- Paths in `webui-user.bat` / scripts are machine-specific (absolute Windows paths).
  When generalizing, call out what the user must edit rather than silently assuming.
- Commit style: conventional commits (`feat:`, `fix:`, `docs:`).
- This is the user's learning project — explain the *why*, prefer readability.

## Scope guardrails (per the user)
Forge only for now. No ComfyUI yet, no LoRAs yet, no wrapper APIs around Forge beyond
the `--api` flag, no Cursor model-picker integration.
