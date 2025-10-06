#!/usr/bin/env python
import pytest
import numpy as np
from pathlib import Path
from packaging import version

version.VERSION_PATTERN

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


class TestImportAndVersion:
    def test_version(self):
        import re
        import elmer_circuitbuilder

        ver = elmer_circuitbuilder.__version__
        assert isinstance(ver, str)
        # Ensure the version can be parsed by packaging (will raise InvalidVersion on failure)
        version.Version(ver)
        # Also assert it matches the canonical VERSION_PATTERN from packaging
        assert re.match(
            rf"^{version.VERSION_PATTERN}$", ver
        ), f"__version__ {ver!r} does not match packaging.VERSION_PATTERN"


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

    @pytest.fixture
    def twocircuits(self):
        c = number_of_circuits(2)
        c[2].ref_node = 2  # non-default ref node for testing
        return c

    def test_number_of_circuits(self, circuit):
        assert len(circuit) == 1

    def test_ref_node(self, circuit):
        assert circuit[1].ref_node == 1

    def test_defuault_ref_node(self, twocircuits):
        assert twocircuits[1].ref_node == 1  # this is the default value
        assert twocircuits[2].ref_node == 2  # set in fixture

    def test_voltage_source(self, circuit, tmp_path: Path):
        """A circuit with only a voltage source should not produce a file, as there are no
        ElmerComponents to write."""
        out = tmp_path / "test_voltage_source.definitions"
        # make sure file doesn't exist before test
        if out.exists():
            out.unlink()
        assert out.exists() is False
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
        """A circuit with a voltage source and an ElmerComponent should produce a file."""

        out = tmp_path / "test_voltage_divider.definitions"
        c = circuit[1]
        v1 = V("V1", 1, 2, 1.0)
        COIL_NAME = "Coil1"
        fem_component = ElmerComponent(COIL_NAME, 2, 1, 1, [1])
        c.components.append([v1, fem_component])
        assert len(c.components[0]) == 2
        assert c.components[0][0].name == "V1"
        assert c.components[0][0].value == 1

        assert c.components[0][1].name == COIL_NAME
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

        # Check for all expected sections in the output
        assert "! Number of Circuits in Model" in text
        assert "$ Circuits = 1" in text
        assert "! Parameters" in text
        assert "$ V1 = 1.0" in text
        assert "! Parameters in Component 1: Coil1" in text
        assert "$ Ns_Coil1 = 1" in text
        assert "! Matrix Size Declaration and Matrix Initialization" in text
        assert "$ C.1.variables = 5" in text
        assert "! Dof/Unknown Vector Definition" in text
        assert '$ C.1.name.1 = "i_V1"' in text
        assert '$ C.1.name.2 = "i_component(1)"' in text
        assert '$ C.1.name.3 = "v_V1"' in text
        assert '$ C.1.name.4 = "v_component(1)"' in text
        assert '$ C.1.name.5 = "u_2_circuit_1"' in text
        assert "! Source Vector Definition" in text
        assert '$ C.1.source.5 = "V1_Source"' in text
        assert "! KCL Equations" in text
        assert "$ C.1.B(0,0) = -1" in text
        assert "$ C.1.B(0,1) = 1" in text
        assert "! KVL Equations" in text
        assert "$ C.1.B(1,2) = 1" in text
        assert "$ C.1.B(1,4) = -1" in text
        assert "$ C.1.B(2,3) = -1" in text
        assert "$ C.1.B(2,4) = 1" in text
        assert "! Component Equations" in text
        assert "$ C.1.B(4,2) = 1" in text
        assert "! Additions in SIF file" in text
        assert f'Name = "{COIL_NAME}"' in text
        assert f'Coil Type = "{c.components[0][1].getCoilType()}"' in text
        assert "Symmetry Coefficient = Real $ 1/(Ns_Coil1)" in text
        assert "! Sources in SIF" in text
        assert "Body Force 1" in text
        assert 'V1_Source = Variable "time"' in text
        assert "! End of Circuit" in text

    def test_two_circuits_with_voltage_divider(self, twocircuits, tmp_path: Path):
        """A test with two circuits to ensure that multiple circuits are handled correctly."""
        out = tmp_path / "test_two_circuits.definitions"
        c1 = twocircuits[1]
        v1 = V("V1", 1, 2, 1.0)
        fem_component1 = ElmerComponent("Coil1", 2, 1, 1, [1])
        c1.components.append([v1, fem_component1])

        c2 = twocircuits[2]
        v2 = V("V2", 1, 2, 5.0)
        fem_component2 = ElmerComponent("Coil2", 2, 1, 1, [2])
        c2.components.append([v2, fem_component2])

        generate_elmer_circuits(twocircuits, str(out))
        # file should be created without error
        text = out.read_text()
        print(text)
        assert "$ Circuits = 2" in text
        assert "$ V1 = 1.0" in text
        assert "$ V2 = 5.0" in text

    @pytest.mark.xfail(
        reason="It is not clear what the intention is if there is one circuit with no ElmerComponents"
    )
    def test_two_circuits_one_with_no_components(self, twocircuits, tmp_path: Path):
        """A test with two circuits to ensure that multiple circuits are handled correctly."""
        out = tmp_path / "test_two_circuits_one_with_no_components.definitions"
        c1 = twocircuits[1]
        v1 = V("V1", 1, 2, 1.0)
        c1.components.append([v1])

        c2 = twocircuits[2]
        v2 = V("V2", 1, 2, 5.0)
        fem_component2 = ElmerComponent("Coil2", 2, 1, 1, [2])
        c2.components.append([v2, fem_component2])

        generate_elmer_circuits(twocircuits, str(out))
        # file should be created without error
        text = out.read_text()
        print(text)
        assert "$ Circuits = 2" in text
        assert "$ V1 = 1.0" in text
        assert "$ V2 = 5.0" in text
