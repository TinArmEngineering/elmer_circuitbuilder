#!/usr/bin/env python
import re
from pathlib import Path

import pytest

from elmer_circuitbuilder import (
    StepwiseResistor,
    Circuit,
    generate_elmer_circuits,
)
from elmer_circuitbuilder.core import create_unknown_name


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
    # exercises numeric path and doesn't produce string-MATC
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


@pytest.mark.parametrize(
    "time,resistance_after,expect_MATAC_string",
    [
        (
            1.0,
            100.0,
            True,
        ),  # should produce a MATC string
        (0.0, 0.0, True),  # should produce a MATC string
        (0.5, 0.0, True),  # should produce a MATC string
        (
            None,
            None,
            False,
        ),  # no time/resistance_after means constant resistance only
        (
            2.0,
            None,
            False,
        ),  # edge case: resistance_after None means constant resistance only
        (None, 50.0, False),  # edge case: time None means constant resistance only
    ],
)
def test_generate_elmer_circuits_writes_stepwise_resistor(
    tmp_path: Path, time, resistance_after, expect_MATAC_string
):
    RESISTANCE_BEFORE = 1e6
    # create stepwise resistor with time variant resistance to ensure MATC string propagates to file
    r = StepwiseResistor(
        "R1", 1, 2, 5, RESISTANCE_BEFORE, time=time, resistance_after=resistance_after
    )
    components = [r]
    c = Circuit(
        1, [components]
    )  # Circuit expects components as a list-containing-the-components-list
    circuits = {1: c}
    out = tmp_path / "elmer_circuit.sif"
    # run generator (should create the file without raising)
    generate_elmer_circuits(circuits, str(out))

    text = out.read_text()
    print(text)
    # file should contain the Component block and the printed Resistance entry
    assert f"Component {r.component_number}" in text
    # For resistor stepwise, write_sif_additions prints "Component  Type = String Resistor" then "Resistance = ..."
    assert "String Resistor" in text or "Component  Type" in text
    assert "Resistance" in text
    # and the MATC expression (or the before/after values) should appear somewhere

    # Allow either a regex pattern (if the test provided one) or a simple substring.
    # When a complex MATC check is required, use a robust regex that:
    #  - permits optional whitespace/newline between the "Resistance" line and the "Real MATC" line
    #  - matches floating point numbers with \d+(?:\.\d+)?
    matc_regex = r"""
        Resistance\s*=\s*Variable\s*time      # first line
        \s*                                   # any whitespace/newline
        Real\s+MATC\s+"if\(tx<                # start of MATC string
        (?P<threshold>\d+(?:\.\d+)?)\)        # threshold value (e.g. 1.0)
        \s*\{(?P<before>\d+(?:\.\d+)?)\}      # value before
        \s*else\s*\{(?P<after>\d+(?:\.\d+)?)\}# value after
        "\s*                                   # trailing quote
    """
    cosnt_regex = r"""
        Resistance\s*=\s*(?P<constant>\d+(?:\.\d+)?)  # constant numeric resistance
    """
    if expect_MATAC_string:
        regexp_str = matc_regex
    else:
        regexp_str = cosnt_regex

    m = re.search(regexp_str, text, re.MULTILINE | re.DOTALL | re.VERBOSE)
    assert m, f"MATC pattern not found in output. Snippet:\n{text[-600:]}"
    # optional: assert numeric groups are what we expect in this param case
    # (use the param values 'time' and 'resistance_after' from the outer test to check)
    if time is not None and resistance_after is not None:
        assert float(m.group("threshold")) == pytest.approx(time)
        print(float(m.group("before")))
        print(float(m.group("after")))
        assert float(m.group("before")) == pytest.approx(RESISTANCE_BEFORE)
        assert float(m.group("after")) == pytest.approx(resistance_after)
