import time
import webbrowser

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
