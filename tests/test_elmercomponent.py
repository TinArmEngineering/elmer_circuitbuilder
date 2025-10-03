from pathlib import Path

import pytest

from elmer_circuitbuilder import (
    ElmerComponent,
    Circuit,
    generate_elmer_circuits,
)
from elmer_circuitbuilder.core import create_unknown_name


def test_elmer_component_basic_properties_and_methods():
    ec = ElmerComponent("EC", 1, 2, component_number=7, master_body_list=[1, "MB"])
    # defaults
    assert ec.component_number == 7
    assert ec.getCoilType() == "Massive"
    assert ec.getNumberOfTurns() == 1
    assert ec.getResistance() == 0
    assert ec.getCoilThickness() == 0
    assert ec.getOpenTerminals() == [None, None]
    assert ec.getTerminalType() is None

    # stranded
    ec.stranded(number_turns=10, resistance=2.5)
    assert ec.getCoilType() == "Stranded"
    assert ec.getNumberOfTurns() == 10
    assert ec.getResistance() == 2.5

    # foil
    ec.foil(number_of_turns=5, coil_thickness=0.12)
    assert ec.getCoilType() == "Foil winding"
    assert ec.getNumberOfTurns() == 5
    assert pytest.approx(ec.getCoilThickness(), 1e-12) == 0.12

    # 3D and open/closed terminal handling
    ec.is3D()
    assert ec.dimension == "3D"
    assert ec.isClosed() is True
    assert ec.isOpen(3, 4) is False
    assert ec.getOpenTerminals() == [3, 4]
    assert ec.getTerminalType() is False


def test_create_unknown_name_includes_component_indices_for_elmer_component():
    ec = ElmerComponent("EC", 1, 2, component_number=7, master_body_list=[1])
    unknown_names, v_comp_rows = create_unknown_name([ec], ref_node=1, circuit_number=1)
    assert f'"i_component({ec.component_number})"' in unknown_names
    assert f'"v_component({ec.component_number})"' in unknown_names
    assert len(v_comp_rows) > 0


def test_generate_elmer_circuits_writes_elmer_component(tmp_path: Path):
    ec = ElmerComponent(
        "EC", 1, 2, component_number=7, master_body_list=[1, "bodyName"]
    )
    components = [ec]
    c = Circuit(1, [components])
    circuits = {1: c}
    out = tmp_path / "elmer_ec.sif"

    # generate file (may exercise string-matrix code paths)
    generate_elmer_circuits(circuits, str(out))

    text = out.read_text()
    # Component block with its number should be present
    assert "Component " + str(ec.component_number) in text
    # Coil type line should be present for ElmerComponent
    assert "Coil Type" in text or "Component  Type" in text
    # parameters section should include Ns_<name>
    assert f"Ns_{ec.name}" in text or "Parameters" in text
