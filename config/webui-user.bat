@echo off

set PYTHON="C:\Users\dhimm\AppData\Local\Programs\Python\Python311\python.exe"
set GIT=
set VENV_DIR=
set COMMANDLINE_ARGS=--api --autolaunch

@REM --- Blackwell (RTX 5080, sm_120) requires torch built for CUDA 12.8 (cu128). ---
@REM Forge's default is torch 2.3.1 on cu121, which will NOT detect a 50-series card.
@REM Pull newest torch/torchvision from the cu128 index (cu128-only wheels = no version-pairing risk).
set TORCH_COMMAND=pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128

@REM Uncomment following code to reference an existing A1111 checkout.
@REM set A1111_HOME=Your A1111 checkout dir
@REM
@REM set VENV_DIR=%A1111_HOME%/venv
@REM set COMMANDLINE_ARGS=%COMMANDLINE_ARGS% ^
@REM  --ckpt-dir %A1111_HOME%/models/Stable-diffusion ^
@REM  --hypernetwork-dir %A1111_HOME%/models/hypernetworks ^
@REM  --embeddings-dir %A1111_HOME%/embeddings ^
@REM  --lora-dir %A1111_HOME%/models/Lora

call webui.bat
