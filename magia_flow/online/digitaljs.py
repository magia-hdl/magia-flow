import subprocess
import time
import webbrowser
from pathlib import Path

import httpx
from magia import Elaborator


def elaborate_on_digitaljs(*modules, server="https://digitaljs.tilk.eu"):
    """
    Elaborate the given modules and open the result in the DigitalJS web app.

    Cautions:
    The elaborated SystemVerilog code will be sent to the DigitalJS service.
    It will be stored on the server and may be used for their own purposes.

    Visit https://github.com/tilk/digitaljs_online and deploy a local instance
    if you are concerned about privacy and want to keep the elaboration local.
    """
    sv_code = Elaborator.to_string(*modules)

    synthesis_payload = {
        "files": {
            "top.sv": sv_code
        },
        "options": {"optimize": True, "fsm": "yes", "fsmexpand": True, "lint": False},
    }

    limits = httpx.Limits(max_keepalive_connections=1, max_connections=1)
    client = httpx.Client(limits=limits)

    synthesis_rsp = client.post(f"{server}/api/yosys2digitaljs", json=synthesis_payload)
    synthesis_rsp = synthesis_rsp.json()
    if "error" in synthesis_rsp:
        failure_msg = "\n".join([synthesis_rsp["error"], synthesis_rsp.get("yosys_stderr", "")])
        raise RuntimeError(f"Synthesis failed: \n {failure_msg}")

    result = synthesis_rsp["output"]
    time.sleep(1)

    store_rsp = client.post(f"{server}/api/storeCircuit", json=result)
    if store_rsp.is_error:
        raise RuntimeError(f"Failed to store circuit: {store_rsp.text}")
    store_rsp = store_rsp.json()
    webbrowser.open_new(f"{server}/#{store_rsp}")


def start_local_server():
    """
    Start a local DigitalJS server.

    This function requires docker compose installed.
    """
    work_dir = (Path(__file__).parent / "digitaljs").absolute()
    docker_compose = _docker_compose_cmd()
    subprocess.run(docker_compose + ["up", "-d", "--build"], cwd=work_dir)  # noqa: S603, S607
    webbrowser.open_new("http://localhost:3000")


def stop_local_server():
    """
    Start a local DigitalJS server.

    This function requires docker compose installed.
    """
    work_dir = (Path(__file__).parent / "digitaljs").absolute()
    docker_compose = _docker_compose_cmd()
    subprocess.run(docker_compose + ["down"], cwd=work_dir)  # noqa: S603, S607


def _docker_compose_cmd():
    try:
        res = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True)  # noqa: S603, S607
        if res.returncode == 0:
            return ["docker", "compose"]
    except FileNotFoundError:
        pass

    try:
        res = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)  # noqa: S603, S607
        if res.returncode == 0:
            return ["docker-compose"]
    except FileNotFoundError:
        pass
    raise RuntimeError("docker compose is not installed")
