"""Public package surface for elmer_circuitbuilder."""

__all__ = [
    "say_hello",
    "number_of_circuits",
    "V",
    "ElmerComponent",
    "generate_elmer_circuits",
]

# package version can be dynamically provided by poetry-dynamic-versioning; default fallback:
__version__ = "0.0.0"

from .core import (
    say_hello,
    number_of_circuits,
    V,
    ElmerComponent,
    generate_elmer_circuits,
)
