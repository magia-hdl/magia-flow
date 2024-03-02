from typing import Optional, Sequence, Union

from magia import Module

from magia_flow.simulation.general import Simulator


def simulate(
        top_level_name: str,
        hdl_modules: Module,
        test_module: Union[str, Sequence[str]],
        python_search_path: Optional[Union[str, Sequence[str]]] = None,
        testcase: Optional[Union[str, Sequence[str]]] = None,
):
    sim = Simulator(top_level_name)
    sim.add_magia_module(hdl_modules)
    sim.compile()
    sim.sim(
        testcase=testcase,
        test_module=test_module,
        python_search_path=python_search_path,
    )


__all__ = [
    "simulate"
]
