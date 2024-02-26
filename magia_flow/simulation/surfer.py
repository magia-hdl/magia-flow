"""
This module provides a function to open a waveform file in the Surfer, a waveform viewer.

Project website: https://surfer-project.org/

Surfer is under the EUPL v1.2 license, which you can obtain from:
https://gitlab.com/surfer-project/surfer/-/blob/main/LICENSE-EUPL-1.2.txt?ref_type=heads
You can obtain its source code from: https://gitlab.com/surfer-project/surfer

In case you does not able to execute the Surfer check the following:
- The Surfer is available for Windows and Linux.
- `openssl` and `libssl-dev` / `openssl-dev` are required to run the Surfer on Linux.
- You may need `root` / Administrator privileges to install the Surfer, without using virtual environments.
"""

import io
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import httpx


def install():
    if shutil.which("surfer"):
        return

    system = platform.system()
    installer_url, install_dir = "", "bin"
    if system == "Windows":
        installer_url = "https://gitlab.com/api/v4/projects/42073614/jobs/artifacts/main/raw/surfer_win.zip?job=windows_build"
        install_dir = "Scripts"
    elif system == "Linux":
        installer_url = "https://gitlab.com/api/v4/projects/42073614/jobs/artifacts/main/raw/surfer_linux.zip?job=linux_build"
    else:
        raise NotImplementedError("Surfer is not available for platform: {system}")

    with httpx.stream("GET", installer_url) as response:
        byte_io = io.BytesIO()
        for chunk in response.iter_bytes():
            byte_io.write(chunk)
        byte_io.seek(0)
        with zipfile.ZipFile(byte_io) as z:
            try:
                z.extractall(Path(sys.prefix, install_dir))
            except PermissionError:
                print("You may need root / Administrator privileges to install the Surfer.")
                print("You can also install it using a virtual environment.")
                raise
            if system == "Linux":
                for name in z.namelist():
                    os.chmod(Path(sys.prefix, install_dir, name), 0o755)


def open_waveform(waveform):
    install()
    subprocess.run(["surfer", waveform])
