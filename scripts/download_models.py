"""One-off downloader for the FLUX.1 [dev] fp8 four-file split (non-gated sources).

Run with your Forge venv's Python:
    venv\\Scripts\\python.exe scripts\\download_models.py
Re-running is safe: files already present are skipped.
"""
import os
from huggingface_hub import hf_hub_download

# EDIT THIS to your Forge install's models folder.
BASE = os.environ.get("FORGE_MODELS_DIR", r"c:\Users\dhimm\Desktop\Image Gen Stack\models")

JOBS = [
    # (repo_id, filename, destination subfolder, save_as or None)
    ("comfyanonymous/flux_text_encoders", "clip_l.safetensors", "text_encoder", None),
    # FLUX.1-schnell/-dev are gated; Kijai's repo ships the same FLUX autoencoder, non-gated.
    ("Kijai/flux-fp8", "flux-vae-bf16.safetensors", "VAE", "ae.safetensors"),
    ("comfyanonymous/flux_text_encoders", "t5xxl_fp8_e4m3fn.safetensors", "text_encoder", None),
    ("Kijai/flux-fp8", "flux1-dev-fp8.safetensors", "Stable-diffusion", None),
]

for repo, fn, sub, save_as in JOBS:
    dest = os.path.join(BASE, sub)
    os.makedirs(dest, exist_ok=True)
    print(f"=== DOWNLOADING {fn}  ({repo}) -> {dest}", flush=True)
    path = hf_hub_download(repo_id=repo, filename=fn, local_dir=dest)
    if save_as:
        target = os.path.join(dest, save_as)
        if os.path.exists(target):
            os.remove(target)
        os.replace(path, target)
        path = target
    size = os.path.getsize(path) / (1024**3)
    print(f"=== DONE {os.path.basename(path)}  ({size:.2f} GB)  -> {path}", flush=True)

print("=== ALL DOWNLOADS COMPLETE", flush=True)
