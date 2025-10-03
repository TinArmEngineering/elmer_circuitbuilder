import pytest
import numpy as np
from types import SimpleNamespace

from elmer_circuitbuilder.core import (
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
