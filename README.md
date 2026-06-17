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
| **Generated images come out solid black** (console shows `invalid value encountered in cast`) | VAE decode starved of VRAM: `flux_GPU_MB` defaults to ~15278 (all but 1GB), so the VAE NaNs at decode | Lower **GPU Weights (MB)** to **~12288** (top of the Forge UI) — frees ~4GB for the VAE. Or set the `flux_GPU_MB` option via the API. **Not** a VAE-precision flag; `--no-half-vae` is a no-op for FLUX |

---

## Appendix: what each error actually was (plain English)

The table above is the quick reference. This section is the *why* — because reading
these and recognizing the **category** of error is the actual skill. Almost none of
these were bugs in anyone's code. They were **integration friction**: a hundred
pieces of third-party software, each frozen at a different version by a different
author, being asked to coexist on one fresh machine. Different muscle from writing
app logic — it's plumbing, not architecture.

A useful frame: most of these are **"old project, new machine"** collisions. Forge is
pinned to roughly the software world of 2024 (Python 3.10, torch 2.3, numpy 1.26). A
brand-new Windows box ships the world of *now* (Python 3.14, newest setuptools, numpy
2.x). Things crack at the boundary between the two.

### 1. "No CUDA device" / cu128 — *bleeding-edge hardware tax*
Your 5080 (Blackwell, `sm_120`) is newer than the defaults most software reaches for.
PyTorch ships builds compiled for specific CUDA versions; the default build predates
Blackwell and literally has no machine code for your chip ("no kernel image
available"). **Lesson:** when you own new hardware, you're ahead of the defaults and
have to point installers at the newer build explicitly. This is the *first* thing to
suspect on any new GPU, and it's recent enough that older AI models and search results
often give stale advice.

### 2. `No module named 'pkg_resources'` (the clip failure) — *a dependency removed a part*
Old packages like `clip` lean on a helper (`pkg_resources`) that ships inside
`setuptools`. Newer `setuptools` **deleted** that helper. So when pip tried to build
`clip` in a clean sandbox using the *latest* setuptools, the thing `clip` reached for
was gone. The fix (`--no-build-isolation`) told pip "don't spin up a clean sandbox with
the newest tools — build it against the older setuptools already in the venv, which
still has the part." **Lesson:** "module not found" during a *build* usually means a
version mismatch in the build tools, not in your code.

### 3. `numpy.dtype size changed` — *an ABI mismatch (the sneaky one)*
numpy ships a compiled C core. Other libraries (here, `scikit-image`) get compiled
*against a specific numpy version's memory layout.* torch quietly pulled in numpy 2.x,
but Forge's scikit-image was built for numpy 1.x — and the internal struct sizes
differ between them (the literal "size changed... expected 96, got 88"). It's not that
a function is missing; it's that two compiled pieces disagree about the *shape of the
bytes*. **Lesson:** "size changed / binary incompatibility" = an **ABI** clash, almost
always numpy. Fix by pinning numpy back to what the consumers expect, not by chasing
the symptom.

### 4. `joblib` missing — *the boring-but-common one*
An optional extension imported a library that simply wasn't installed. `pip install
joblib`, done. **Lesson:** plain `ModuleNotFoundError` at *runtime* (not during a
build) usually means exactly what it says — install the missing package.

### 5. `'webui-user.bat' is not recognized` — *the machine being weird*
This one wasn't Forge's fault or the ecosystem's. Your shell had
`NoDefaultCurrentDirectoryInExePath=1` set — an unusual hardening flag that tells
Windows "do **not** look in the current folder for programs to run." So a script
sitting *right there* was invisible to the command that tried to call it. The launcher
clears the flag. **Lesson:** when something is impossible ("the file is *right there*"),
suspect an environment setting, not the file. These send you down the longest rabbit
holes precisely because they defy common sense until you find the one obscure variable.

### 6. Gated model repos — *a policy change upstream*
The "official" FLUX download paths (Black Forest Labs' repos) were locked behind a
login/terms wall *after* the guides were written. Not a technical error at all — just
the world moving. We routed to non-gated mirrors with the identical weights.
**Lesson:** "401 / access restricted" on a download is a *permissions* problem, not a
broken link — either authenticate or find an open mirror.

### 7. Solid black images — *resource starvation, not a "bug"*
After everything installed and ran, the *output* came out pure black. The console
showed `invalid value encountered in cast` — meaning the final image tensor was full
of **NaN** ("not a number") and turned black when converted to pixels. The cause
wasn't the model or precision: Forge's `flux_GPU_MB` (the "GPU Weights" slider)
defaulted to ~15.3 GB of the 16 GB card, leaving the **VAE** (the part that turns the
math into a picture) only ~1 GB at decode time — so it overflowed into NaN. Dropping
GPU Weights to ~12 GB gave the VAE room and fixed it. **Lesson:** on a memory-tight
GPU, "garbage/black/NaN output" with *no crash* often means a stage got **starved of
VRAM**, not that anything is broken — look at how memory is partitioned, not at the
model. (Tell-tale sign it's *not* precision: `--no-half-vae` had no effect, because
Forge auto-manages the FLUX VAE dtype to bf16 regardless.)

**The meta-pattern:** when a build like this fails, the first move is to *classify the
error* — hardware/driver? build-tool version? ABI? missing package? environment
setting? permissions? resource starvation? — because each class has its own standard
fix. The traceback almost always tells you which bucket you're in if you read the
*last* few lines, not the scary wall in the middle.

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
