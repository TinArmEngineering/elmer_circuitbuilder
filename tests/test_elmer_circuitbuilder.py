#!/usr/bin/env python
import pytest
import numpy as np
from pathlib import Path

"""Tests for `elmer_circuitbuilder` package."""


from elmer_circuitbuilder import say_hello


def test_helloworld_no_params():
    assert say_hello() == "Hello, World!"


def test_helloworld_with_param():
    assert say_hello("Everyone") == "Hello, Everyone!"


from elmer_circuitbuilder import (
    number_of_circuits,
    V,
    ElmerComponent,
    generate_elmer_circuits,
)


class TestBasicCircuit:
    def test_version_of_numpy(self):
        """This test can probably be removed later, but for now it ensures that the tests are run
        in the Poetry environment where numpy 2.3.x is installed, avoiding numpy ufunc
        """
        ver = np.__version__
        major, minor, *_ = map(int, ver.split("."))
        assert (major, minor) == (
            2,
            3,
        ), f"Run tests in the project's Poetry env with numpy 2.3.x (found {ver})"

    @pytest.fixture
    def circuit(self):
        c = number_of_circuits(1)
        c[1].ref_node = 1
        return c

    def test_number_of_circuits(self, circuit):
        assert len(circuit) == 1

    def test_ref_node(self, circuit):
        assert circuit[1].ref_node == 1

    def test_voltage_source(self, circuit, tmp_path: Path):
        out = tmp_path / "circuit1.definitions"
        c = circuit[1]
        v1 = V("V1", 1, 2, 1.0)

        c.components.append([v1])
        assert len(c.components[0]) == 1
        assert c.components[0][0].name == "V1"
        assert c.components[0][0].value == 1

        generate_elmer_circuits(circuit, str(out))
        # file should not be created as without ElmerComponents there is nothing to write
        assert out.exists() is False

    def test_voltage_divider(self, circuit, tmp_path: Path):
        out = tmp_path / "circuit.definitions"
        c = circuit[1]
        v1 = V("V1", 1, 2, 1.0)
        fem_component = ElmerComponent("Coil1", 2, 1, 1, [1])
        c.components.append([v1, fem_component])
        assert len(c.components[0]) == 2
        assert c.components[0][0].name == "V1"
        assert c.components[0][0].value == 1

        assert c.components[0][1].name == "Coil1"
        assert c.components[0][1].component_number == 1
        assert c.components[0][1].master_bodies == [1]
        assert c.components[0][1].getCoilType() == "Massive"
        assert c.components[0][1].getNumberOfTurns() == 1
        assert c.components[0][1].getResistance() == 0
        assert c.components[0][1].getCoilThickness() == 0
        assert c.components[0][1].getOpenTerminals() == [None, None]
        assert c.components[0][1].getTerminalType() is None
        assert c.components[0][1].dimension == "2D"
        assert c.components[0][1].isClosed() is True

        generate_elmer_circuits(circuit, str(out))
        # file should be created without error
        text = out.read_text()
        print(text)
        assert "$ V1 = 1.0" in text
