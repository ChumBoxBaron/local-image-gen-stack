# Local Image-Gen Stack — Forge + FLUX.1 on an RTX 5080

My working setup for running **local AI image generation** on a Windows PC with an
**RTX 5080 (16 GB, Blackwell)** — [Forge](https://github.com/lllyasviel/stable-diffusion-webui-forge)
as the engine and **FLUX.1 [dev] fp8** as the model. First image lands in ~25–30 s,
fully offline, no per-image cost.

This repo is the **recipe**, not a fork of Forge. It holds my config, helper
scripts, and the hard-won troubleshooting notes — enough to reproduce the build on
a fresh machine by cloning Forge and applying these files.

> **Mental model (farm metaphor):** the GPU + model weights are the *ox*, Forge is
> the *yoke* (inference engine), and the browser tab at `:7860` is the *cockpit*.
> This is a separate rig from my text stack (Ollama + Open WebUI) — different ox,
> different yoke.

---

## Hardware this targets

| | |
|---|---|
| GPU | NVIDIA RTX 5080, 16 GB VRAM (Blackwell, compute capability **sm_120**) |
| CPU / RAM | Ryzen 9 9950X3D / 64 GB |
| OS | Windows 11 |

The single most important fact: **Blackwell (50-series) needs PyTorch built for
CUDA 12.8 (`cu128`).** Older torch can't see the card and fails with a cryptic
"no CUDA device" / "no kernel image available" error. See [the gotcha](#the-blackwell-gotcha-read-this-first).

---

## Quick start (fresh machine)

1. **Prereqs:** current NVIDIA driver, **Python 3.11** (3.10 also fine — *not* 3.12+),
   and Git. Confirm the GPU with `nvidia-smi`.
2. **Clone Forge:**
   ```bat
   git clone https://github.com/lllyasviel/stable-diffusion-webui-forge.git
   ```
3. **Apply this repo's config** — copy [`config/webui-user.bat`](config/webui-user.bat)
   and [`config/run_forge.bat`](config/run_forge.bat) into the Forge folder.
   Edit the Python path in `webui-user.bat` to match your machine (see comments in
   the file).
4. **First launch** builds the venv and installs `cu128` torch + dependencies:
   ```bat
   run_forge.bat
   ```
   If the build hits the `clip` / `numpy` / `joblib` snags, apply
   [the dependency fixes](#dependency-fixes-applied-once) — then run again.
5. **Verify CUDA before downloading models** (don't skip this):
   ```bat
   venv\Scripts\python.exe -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
   ```
   You want a `+cu128` version, `True`, and your GPU name. If not, **stop and fix torch.**
6. **Download FLUX** (4-file split, non-gated sources):
   ```bat
   venv\Scripts\python.exe scripts\download_models.py
   ```
7. **Generate.** `run_forge.bat` opens a browser tab at http://127.0.0.1:7860.
   Pick the FLUX checkpoint, add the encoders/VAE, type a prompt. See
   [FLUX settings](#flux-settings-that-matter).

---

## The Blackwell gotcha (read this first)

Forge's default install pins **torch 2.3.1 on cu121**, which **cannot detect a
50-series card.** `config/webui-user.bat` overrides this:

```bat
set TORCH_COMMAND=pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
```

Pulling from the `cu128` index (rather than pinning a version) means every wheel it
grabs is Blackwell-compatible — no version-pairing guesswork. Verified working with
**torch 2.11.0+cu128**.

---

## Model files — where they go

Download with [`scripts/download_models.py`](scripts/download_models.py). FLUX is
split across four files (unlike a single SDXL checkpoint):

| File | Folder | Source (non-gated) |
|---|---|---|
| `flux1-dev-fp8.safetensors` (transformer, ~12 GB) | `models\Stable-diffusion\` | `Kijai/flux-fp8` |
| `clip_l.safetensors` (CLIP-L encoder) | `models\text_encoder\` | `comfyanonymous/flux_text_encoders` |
| `t5xxl_fp8_e4m3fn.safetensors` (T5-XXL encoder) | `models\text_encoder\` | `comfyanonymous/flux_text_encoders` |
| `ae.safetensors` (VAE) | `models\VAE\` | `Kijai/flux-fp8` (`flux-vae-bf16`, renamed) |

> **Why not the official Black Forest Labs repo?** `black-forest-labs/FLUX.1-dev`
> *and* `FLUX.1-schnell` are now **gated** (require an HF login + accepting terms).
> The mirrors above are the same weights, openly downloadable. The VAE is the FLUX
> autoencoder either way.

Drop any future models/LoRAs into the matching folder and hit the 🔄 refresh in the UI.

---

## FLUX settings that matter

- **Checkpoint:** select `flux1-dev-fp8.safetensors` (top-left dropdown).
- **VAE / Text Encoder** selector: add all three — `ae`, `clip_l`, `t5xxl_fp8_e4m3fn`.
- **CFG Scale = 1**, and put your guidance in **Distilled CFG Scale ≈ 3.5.**
  FLUX uses *distilled* guidance; cranking real CFG like SDXL doubles compute and
  degrades output.
- **Steps:** ~24 · **Resolution:** 1344×768 (16:9) or 1024×1024 · **Sampler:** Euler · **Schedule:** Simple.

**Text in images:** FLUX (and SDXL) are unreliable at rendering precise text. For
labeled diagrams, generate the illustration only, then add labels in Figma /
Excalidraw / Canva.

---

## Dependency fixes (applied once)

Modern Python + a fresh Forge clone hit a few snags. Each is a one-time fix in the venv:

| Symptom | Cause | Fix |
|---|---|---|
| `'webui-user.bat' is not recognized` even from inside the folder | Shell has `NoDefaultCurrentDirectoryInExePath=1`, so cmd won't search the current dir | Launch via `run_forge.bat`, which clears it and `cd`s to the repo |
| `Couldn't install clip` / `No module named 'pkg_resources'` | `clip` & `open_clip` build under newest setuptools, which dropped `pkg_resources` | `pip install --no-build-isolation <the two github zips>` (uses venv's older setuptools) |
| UI crash: `numpy.dtype size changed` | torch pulled numpy 2.x; old `scikit-image` is numpy-1 ABI | `pip install numpy==1.26.2` (Forge's intended pin) |
| Soft-inpainting extension import error | `joblib` missing | `pip install joblib` |
| `INCOMPATIBLE PYTHON VERSION` warning on 3.11 | Forge is tested on 3.10 | Cosmetic — ignore |

---

## Measured performance (RTX 5080, this config)

| Metric | Value |
|---|---|
| torch / CUDA | 2.11.0+cu128, `cuda.is_available()` True, sm_120 |
| First generation | ~45 s (includes one-time model load) |
| Steady-state generation | **~29 s** @ 1344×768, 24 steps (~1.0 s/it) |
| Peak VRAM | **~12.8 GB / 16 GB** — T5 offloads to system RAM, no OOM |

---

## Repo layout

```
config/
  webui-user.bat   # Forge env config: Python 3.11 pin, cu128 torch, --api --autolaunch
  run_forge.bat    # launcher (clears the NoDefaultCurrentDirectory quirk, cd's to repo)
scripts/
  download_models.py  # fetch the FLUX 4-file split from non-gated sources
  smoke_test.py       # API generation test (1344x768, 24 steps, distilled CFG 3.5)
```

The actual Forge install (and its `venv/` and multi-GB `models/`) lives separately
and is **not** in this repo.

---

## Roadmap / intentionally not done yet

- ComfyUI (node-graph pipelines) — later, once comfortable with Forge.
- Style LoRAs from CivitAI — base FLUX first.
- No wrapper scripts/APIs around Forge beyond the built-in `--api` flag.

---

## License

MIT — see [LICENSE](LICENSE). It covers my config and scripts only; Forge, FLUX, and
the model weights carry their own licenses.
