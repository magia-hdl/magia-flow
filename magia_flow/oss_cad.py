import logging
import platform
import sys
import tarfile
from tempfile import NamedTemporaryFile

import httpx


def install(
        verilator: bool = False,
        pnr: bool = False,
):
    logger = logging.getLogger(__name__)

    system = platform.system()

    if system != "Linux":
        raise NotImplementedError("Only Linux is supported for now.")
    if sys.prefix == sys.base_prefix:
        raise RuntimeError("You must use a virtual environment to install the OSS-CAD Suite.")

    installer_url = (
        "https://github.com/YosysHQ/oss-cad-suite-build/releases/download/"
        "2024-02-28/oss-cad-suite-linux-x64-20240228.tgz"
    )

    logger.info("Downloading the OSS-CAD Binary...")
    with httpx.stream("GET", installer_url, follow_redirects=True) as response, NamedTemporaryFile(
            suffix=".tgz") as temp_file:
        for chunk in response.iter_bytes(chunk_size=16 * 1024 * 1024):
            temp_file.write(chunk)
        temp_file.flush()

        logger.info("Extracting files...")
        with tarfile.open(temp_file.name, mode="r:gz") as t:
            members = [
                tinfo.replace(name=tinfo.name.removeprefix("oss-cad-suite/"))
                for tinfo in t.getmembers()
                if (tname := tinfo.name) != "oss-cad-suite" and
                   "__pycache__" not in tname and
                   ("verilator" not in tname or verilator) and
                   "examples" not in tname and (
                           (
                                   "nextpnr" not in tname and
                                   "icebox" not in tname and
                                   "prjoxide" not in tname and
                                   "trellis" not in tname
                           ) or pnr
                   )
            ]
            t.extractall(sys.prefix, members)  # noqa: S202
