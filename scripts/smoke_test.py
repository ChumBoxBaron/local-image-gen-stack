"""First FLUX test generation via Forge API. Measures wall-clock and saves the image.

Forge must be running with --api (see config/webui-user.bat). Then:
    venv\\Scripts\\python.exe scripts\\smoke_test.py
"""
import base64, time, json, os, urllib.request

BASE = "http://127.0.0.1:7860"

# EDIT THIS to your Forge install's models folder.
MODELS = os.environ.get("FORGE_MODELS_DIR", r"C:\Users\dhimm\Desktop\Image Gen Stack\models")
MODULES = [
    os.path.join(MODELS, "VAE", "ae.safetensors"),
    os.path.join(MODELS, "text_encoder", "clip_l.safetensors"),
    os.path.join(MODELS, "text_encoder", "t5xxl_fp8_e4m3fn.safetensors"),
]

def post(path, payload, timeout=600):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

payload = {
    "prompt": "a watercolor of a red barn in a wheat field",
    "negative_prompt": "",
    "width": 1344, "height": 768,
    "steps": 24,
    "cfg_scale": 1,
    "distilled_cfg_scale": 3.5,
    "sampler_name": "Euler",
    "scheduler": "Simple",
    "override_settings": {
        "sd_model_checkpoint": "flux1-dev-fp8.safetensors",
        "forge_additional_modules": MODULES,
    },
    "override_settings_restore_afterwards": False,
}

print("=== submitting txt2img (first call includes model load) ...", flush=True)
t0 = time.time()
res = post("/sdapi/v1/txt2img", payload)
elapsed = time.time() - t0
img_b64 = res["images"][0]
out = os.path.join(os.getcwd(), "smoke_test_output.png")
with open(out, "wb") as f:
    f.write(base64.b64decode(img_b64.split(",", 1)[-1]))
print(f"=== GENERATION OK in {elapsed:.1f}s -> {out}", flush=True)
info = json.loads(res.get("info", "{}"))
print("=== sampler:", info.get("sampler_name"), "| steps:", info.get("steps"),
      "| size:", f"{info.get('width')}x{info.get('height')}", flush=True)
