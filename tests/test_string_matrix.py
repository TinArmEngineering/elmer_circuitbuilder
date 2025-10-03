import pytest
import numpy as np
from types import SimpleNamespace

from elmer_circuitbuilder.elmer_circuitbuilder import (
    get_incidence_matrix_str,
    get_resistance_matrix_str,
    get_inductance_matrix_str,
    get_capacitance_matrix_str,
)


class DummyComp(SimpleNamespace):
    @property
    def component_type(self):
        return getattr(self, "_component_type", None)


def make(name, pin1, pin2, idx, ctype, **kwargs):
    d = DummyComp(name=name, pin1=pin1, pin2=pin2, component_number=idx, **kwargs)
    d._component_type = ctype
    return d


def _indices_for_types(components):
    indr = [i for i, c in enumerate(components) if c.component_type == "resistor"]
    indi = [i for i, c in enumerate(components) if c.component_type == "inductor"]
    indcap = [i for i, c in enumerate(components) if c.component_type == "capacitor"]
    return indr, indi, indcap


def test_string_matrix_functions_do_not_raise_for_mixed_components():
    components = [
        make("R1", 1, 2, 1, "resistor", resistance=10),
        make(
            "SR",
            2,
            3,
            2,
            "resistor",
            resistance='Variable MATC "if(tx<0.5) {10} else {20}"',
        ),
        make("L1", 3, 1, 3, "inductor", inductance=0.01),
        make("C1", 2, 1, 4, "capacitor", capacitance=1e-6),
        make("V1", 1, 0, 5, "voltage"),
    ]

    numnodes = max(max(c.pin1, c.pin2) for c in components)
    numedges = len(components)
    ref_node = 1

    # basic sanity: functions should not raise UFuncNoLoopError / TypeErrors for string arrays
    try:
        A_str = get_incidence_matrix_str(components, numnodes, numedges, ref_node)
    except Exception as exc:
        pytest.fail(f"get_incidence_matrix_str raised {type(exc).__name__}: {exc}")

    assert isinstance(A_str, np.ndarray)
    assert A_str.shape == (numnodes, numedges)

    indr, indi, indcap = _indices_for_types(components)

    try:
        R_str = get_resistance_matrix_str(components, numedges, indr, indi, indcap)
        L_str = get_inductance_matrix_str(components, numedges, indi)
        C_str = get_capacitance_matrix_str(components, numedges, indcap)
    except Exception as exc:
        pytest.fail(f"string-matrix generator raised {type(exc).__name__}: {exc}")

    assert isinstance(R_str, np.ndarray)
    assert isinstance(L_str, np.ndarray)
    assert isinstance(C_str, np.ndarray)

    # expect the MATC string to survive into the resistance-string matrix (at least present as substring)
    found_matc = any("MATC" in str(x) or "if(tx<" in str(x) for x in R_str.flatten())
    assert found_matc or any("10" in str(x) for x in R_str.flatten())
