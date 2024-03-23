import os
import shutil
import string
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable, Literal

from magia import Elaborator


def sby_installed() -> bool:
    """
    Check if SymbiYosys is installed
    """
    if not shutil.which("sby"):
        return False
    return True


class SbyTask:
    extra_code_counter = 0
    extra_file_template = string.Template("[file $fname]\n$code\n")
    read_file_template = string.Template('read -formal "$fname"\n')
    section_template = string.Template("[$section]\n$content\n")

    cmd_template = string.Template('sby -f -d "$workdir" "$sby_file"')

    @dataclass
    class SbyTaskSpec:
        """
        Describes a SymbiYosys task to be executed
        """
        name: str = "default"
        top_module: str = None
        mode: Literal["prove", "cover", "bmc", "live"] = "bmc"
        engines: list[str] = field(default_factory=list)
        options: list[str] = field(default_factory=list)
        script: list[str] = field(default_factory=list)
        files: list[str] = field(default_factory=list)
        extra_code: dict[str, str] = field(default_factory=dict)

        def __post_init__(self):
            if self.top_module is None:
                raise ValueError("top_module is required")
            self.script.append(f"prep -top {self.top_module}")

            if len(self.engines) == 0:
                if self.mode == "live":
                    self.engines.append("aiger suprove")
                else:
                    self.engines.append("smtbmc boolector")

            self.options = [f"mode {self.mode}"] + self.options

    @dataclass
    class SbyTaskResult:
        """
        Describes the result of a SymbiYosys task
        """
        passed: bool
        raw_result: str = field(repr=False)
        stdout: str = field(repr=False)
        stderr: str = field(repr=False)
        tests: list[dict]
        test_count: int
        failures: int
        errors: int
        skipped: int

    def __init__(self, top_module: str, mode="bmc", work_dir=None, **kwargs):
        self.spec = self.SbyTaskSpec(top_module=top_module, mode=mode)
        self.work_dir: Path = work_dir
        if self.work_dir is None:
            self.work_dir = Path.cwd().absolute()

        self._task_executed = False
        self._result = None

    def add_file(self, *files: Iterable[os.PathLike]):
        """
        Add files to the task
        """
        self.spec.files += [
            str(Path(file).absolute())
            for file in files
        ]

    def add_code(self, code: str, name=None):
        """
        Add extra code to the task
        """
        if not name:
            name = f"extra_code_{self.extra_code_counter}.sv"
            self.extra_code_counter += 1

        if os.pathsep in name:
            raise ValueError("The name cannot be an absolute/relative path")
        if name in self.spec.extra_code:
            raise ValueError(f"Code with name '{name}' already exists")

        self.spec.extra_code[name] = code

    def add_script(self, *script: Iterable[str]):
        """
        Add script lines to the task
        """
        self.spec.script += list(script)

    def _generate_script(self):
        """
        Generate the SymbiYosys script
        """
        extra_code = [
            self.extra_file_template.substitute(fname=fname, code=code)
            for fname, code in self.spec.extra_code.items()
        ]
        flist = self.spec.files + list(self.spec.extra_code.keys())
        read_file_scripts = [
            self.read_file_template.substitute(fname=fname)
            for fname in flist
        ]

        section_formation = {
            "tasks": [f"{self.spec.name}"],
            "options": self.spec.options,
            "engines": self.spec.engines,
            "script": read_file_scripts + self.spec.script,
        }
        sections = [
                       self.section_template.substitute(section=section, content="\n".join(content))
                       for section, content in section_formation.items()
                   ] + extra_code

        return "\n".join(sections)

    def run(self):
        """
        Run the task. Override work_dir if it is provided
        """
        work_dir = self.work_dir / self.spec.top_module
        with NamedTemporaryFile("w", suffix=".sby") as sby_file:
            sby_script = self._generate_script()
            sby_file.write(sby_script)
            sby_file.flush()

            cmd = self.cmd_template.substitute(task_name=self.spec.name, workdir=str(work_dir), sby_file=sby_file.name)
            subprocess.run(cmd, shell=True, capture_output=True)  # noqa: S602

        self._task_executed = True
        self._capture_result()

    def _capture_result(self):
        """
        Capture the result of the task
        """
        if not self._task_executed:
            raise ValueError("Run the task first")
        output_file = next(self.work_dir.rglob(f"**/*{self.spec.name}.xml"))
        raw_xml = output_file.read_text()
        root = ET.fromstring(raw_xml)

        stdout = ""
        stderr = ""
        success, errors, failures, skipped = 0, 0, 0, 0
        tests = []

        for testsuite in root.iter("testsuite"):
            stdout += testsuite.find("system-out").text + "\n"
            stderr += testsuite.find("system-err").text + "\n"
            for testcase in testsuite.iter("testcase"):
                new_test = {
                    "id": testcase.get("id", ""),
                    "classname": testcase.get("classname", ""),
                    "desc": testcase.get("name", ""),
                    "loc": testcase.get("location", ""),
                    "status": "passed",
                    "info": {}
                }
                if testcase.find("skipped") is not None:
                    skipped += 1
                    new_test["status"] = "skipped"
                elif (node := testcase.find("failure")) is not None:
                    failures += 1
                    new_test["status"] = "failed"
                    new_test["info"] = {
                        "type": node.get("type", ""),
                        "message": node.get("message", ""),
                    }
                elif (node := testcase.find("error")) is not None:
                    errors += 1
                    new_test["status"] = "error"
                    new_test["info"] = {
                        "type": node.get("type", ""),
                        "message": node.get("message", ""),
                    }
                tests.append(new_test)

        self._result = self.SbyTaskResult(
            passed=errors == 0 and failures == 0,
            raw_result=raw_xml,
            stdout=stdout, stderr=stderr,
            test_count=len(tests),
            tests=tests,
            failures=failures, errors=errors, skipped=skipped,
        )

    @property
    def result(self):
        """
        Get the result of the task
        """
        if not self._task_executed:
            raise ValueError("Run the task first")
        return self._result

    @classmethod
    def from_module(cls, top_module: str, *modules: Iterable[str], **kwargs):
        """
        Create a SbyTask from a list of modules
        """
        task = cls(top_module=top_module, **kwargs)
        code = Elaborator.to_string(*modules)
        task.add_code(code, "elaborated.sv")
        return task

    @classmethod
    def from_code(cls, top_module: str, code: str, **kwargs):
        """
        Create a SbyTask from a code string
        """
        task = cls(top_module=top_module, **kwargs)
        task.add_code(code, "manual_code.sv")
        return task
