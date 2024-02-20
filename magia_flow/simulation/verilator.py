import os
import shutil
import subprocess
import sys
from pathlib import Path


def init_verilator():
    """
    Initialize Verilator in virtual environment for cocotb tests
    """
    if not (verilator := shutil.which("verilator")):
        raise RuntimeError("Verilator not found in PATH")

    version = subprocess.check_output([verilator, "--version"]).decode().strip().split()[1]  # noqa: S603
    if float(version) < 5.006:
        raise RuntimeError("Verilator version >= 5.006 is required")

    # Skip if not in venv
    if sys.base_prefix == sys.prefix:
        return

    # Check if verilator is already copied into venv
    verilator_mounted = Path(sys.prefix, "bin", "verilator").exists()
    if not verilator_mounted:
        # Locate Verilator binaries and the original VERILATOR_ROOT
        verilator_bin_location = Path(shutil.which("verilator_bin")).parent
        verilator_root = Path(
            subprocess.check_output([verilator, "--getenv", "VERILATOR_ROOT"]).decode().strip()  # noqa: S603
        )
        verilator_bins = list(verilator_bin_location.glob("verilator*"))

        # Copy files into venv
        shutil.copytree(verilator_root, Path(sys.prefix), dirs_exist_ok=True)
        for path in verilator_bins:
            shutil.copy(path, Path(sys.prefix, "bin"))

        # Patch verilated.mk
        # Replace the Python3 interpreter with the one in venv
        makefile_in = Path(sys.prefix, "include", "verilated.mk")
        makefile_content = makefile_in.read_text().splitlines()
        for i, line in enumerate(makefile_content):
            if line.startswith("PYTHON3 ="):
                makefile_content[i] = f"PYTHON3 = {sys.executable}"
                break
        makefile_in.write_text("\n".join(makefile_content))

    # Override VERILATOR_ROOT
    os.environ["VERILATOR_ROOT"] = sys.prefix
