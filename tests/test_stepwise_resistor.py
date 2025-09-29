#!/usr/bin/env python
import re
from pathlib import Path

import pytest

from elmer_circuitbuilder.elmer_circuitbuilder import (
    StepwiseResistor,
    Circuit,
    create_unknown_name,
    generate_elmer_circuits,
)


def test_stepwise_resistor_basic_properties():
    r = StepwiseResistor("R1", 1, 2, 5, 10)
    # When no time/resistance_after given, resistance should be the numeric string
    assert r.resistance == "10"
    assert r.component_type == "resistor"


def test_stepwise_resistor_time_variant_resistance():
    r = StepwiseResistor("R1", 1, 2, 5, 10, time=0.5, resistance_after=20)
    res = r.resistance
    # Should produce a MATC variable string containing the conditional and both values
    assert "MATC" in res
    assert "if(tx<" in res
    assert "10" in res and "20" in res


def test_create_unknown_name_includes_component_indices():
    r = StepwiseResistor("R1", 1, 2, 5, 10)
    components = [r]
    unknown_names, v_comp_rows = create_unknown_name(
        components, ref_node=1, circuit_number=1
    )
    # unknown names for elmer components use component_number in i_component(...) and v_component(...)
    assert f'"i_component({r.component_number})"' in unknown_names
    assert f'"v_component({r.component_number})"' in unknown_names
    # ensure v_comp_rows contains at least one index (voltage row for the component)
    assert len(v_comp_rows) > 0


def test_generate_elmer_circuits_writes_const_resistor(tmp_path: Path):
    # Use a plain numeric resistor (no time/resistance_after) so generator
    # exercises numeric path and doesn't produce string-MATC arrays that
    # may trigger NumPy ufunc errors.
    r = StepwiseResistor("R1", 1, 2, 5, 10)  # plain numeric resistance
    components = [r]
    c = Circuit(
        1, [components]
    )  # Circuit expects components as a list-containing-the-components-list
    circuits = {1: c}
    out = tmp_path / "elmer_circuit.sif"
    # run generator (should create the file without raising)
    generate_elmer_circuits(circuits, str(out))

    text = out.read_text()
    # file should contain the Component block and the printed Resistance entry
    assert f"Component {r.component_number}" in text
    assert "Resistance" in text
    # numeric resistance value should appear in the output
    assert "10" in text


def test_generate_elmer_circuits_writes_stepwise_resistor(tmp_path: Path):
    # create stepwise resistor with time variant resistance to ensure MATC string propagates to file
    r = StepwiseResistor("R1", 1, 2, 5, 10, time=0.25, resistance_after=15)
    components = [r]
    c = Circuit(
        1, [components]
    )  # Circuit expects components as a list-containing-the-components-list
    circuits = {1: c}
    out = tmp_path / "elmer_circuit.sif"
    # run generator (should create the file without raising)
    generate_elmer_circuits(circuits, str(out))

    text = out.read_text()
    # file should contain the Component block and the printed Resistance entry
    assert f"Component {r.component_number}" in text
    # For resistor stepwise, write_sif_additions prints "Component  Type = String Resistor" then "Resistance = ..."
    assert "String Resistor" in text or "Component  Type" in text
    assert "Resistance" in text
    # and the MATC expression (or the before/after values) should appear somewhere
    assert "if(tx<" in text or ("10" in text and "15" in text)
