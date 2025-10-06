"""Public package surface for elmer_circuitbuilder."""

__all__ = [
    "Component",
    "R",
    "V",
    "I",
    "L",
    "C",
    "ElmerComponent",
    "StepwiseResistor",
    "Circuit",
    "number_of_circuits",
    "generate_elmer_circuits",
    "say_hello",
    "__version__",
]

# When the package is installed, the dynamic version will be written into the distribution metadata.
# Prefer generated file written by poetry-dynamic-versioning
try:
    from ._version import __version__  # generated at build/install time
except Exception:
    # fallback to distribution metadata when installed; final fallback is "0.0.0"
    __version__ = "0.0.0"
    try:
        from importlib.metadata import version as _get_version, PackageNotFoundError
    except Exception:
        _get_version = None
        PackageNotFoundError = Exception
    if _get_version is not None:
        try:
            __version__ = _get_version("elmer_circuitbuilder")
        except PackageNotFoundError:
            pass

# Import the public API from the implementation module (core)
try:
    from .core import (  # type: ignore
        Component,
        R,
        V,
        I,
        L,
        C,
        ElmerComponent,
        StepwiseResistor,
        Circuit,
        number_of_circuits,
        generate_elmer_circuits,
        say_hello,
    )
except Exception as exc:  # give a clear import-time error
    raise ImportError(
        "elmer_circuitbuilder: failed to import implementation from src/elmer_circuitbuilder/core.py; "
        "ensure the file exists and defines the expected public names. Original error: "
        f"{exc}"
    )
