import inspect
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Sequence, Union

import cocotb.runner
from magia import Elaborator, Module


class Simulator:
    def __init__(
            self, hdl_toplevel,
            build_dir: Optional[os.PathLike] = None,
            simulator: str = "verilator",
    ):
        self.simulator_type = simulator
        self.runner = cocotb.runner.get_runner(simulator)

        self._temp_build_dir = TemporaryDirectory(prefix="sim_magia_") if build_dir is None else None
        self.build_dir = self._temp_build_dir.name if build_dir is None else build_dir

        self.output_file = f"{self.build_dir}/magia.generated.sv"
        self.top_level = hdl_toplevel
        self.source_files = []
        self.elaborated_sv = []

    def add_source(self, source_file: os.PathLike):
        self.source_files.append(source_file)

    def add_magia_module(self, *module: Module):
        self.elaborated_sv.append(
            Elaborator.to_string(*module)
        )

    def compile(self, waves: bool = False, **kwargs):
        if waves:
            kwargs["build_args"] = kwargs.get("build_args", []) + ["--trace", "--trace-fst"]

        with open(self.output_file, mode="w") as f:
            f.write("\n\n".join(self.elaborated_sv))
        self.runner.build(
            verilog_sources=self.source_files + [self.output_file],
            hdl_toplevel=self.top_level,
            always=True,
            build_dir=self.build_dir,
            **kwargs
        )

    def sim(
            self,
            test_module: Union[str, Sequence[str]],
            python_search_path: Optional[Union[str, Sequence[str]]] = None,
            testcase: Optional[Union[str, Sequence[str]]] = None,
            waves: bool = False,
            **kwargs
    ):
        if waves:
            if self.simulator_type == "verilator":
                kwargs["test_args"] = kwargs.get("test_args", []) + ["--trace", "--trace-fst"]
            else:
                kwargs["waves"] = waves

        with self._patch_sys_path(python_search_path):
            return self.runner.test(
                hdl_toplevel=self.top_level,
                test_module=test_module,
                testcase=testcase,
                build_dir=self.build_dir,
                test_dir=self.build_dir,
                results_xml="results.xml",
                **kwargs
            )

    @property
    def wave_file(self):
        if self.simulator_type == "verilator":
            return Path(self.build_dir, "dump.fst")
        raise NotImplementedError("Wave file not supported for this simulator")

    @staticmethod
    def current_dir():
        """
        Return the directory of the caller script file
        """
        caller_frame = inspect.stack()[1]
        return str(Path(caller_frame.filename).parent.absolute())

    @staticmethod
    def current_package():
        """
        Return the package name of the caller script file
        """
        caller_frame = inspect.stack()[1]
        return str(Path(caller_frame.filename).stem)

    @staticmethod
    @contextmanager
    def _patch_sys_path(paths):
        cur_paths = sys.path
        if paths:
            if isinstance(paths, str):
                paths = [paths]
            sys.path = paths + cur_paths
        yield
        sys.path = cur_paths
