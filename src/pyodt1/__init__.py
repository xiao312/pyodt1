"""pyodt1: Python reimplementation of the Basic ODT package."""

from pyodt1.legacy import b_add_term, b_init_stats, b_read_options, brng_get, brng_put, run_legacy_case

__all__ = [
    "__version__",
    "b_add_term",
    "b_init_stats",
    "b_read_options",
    "brng_get",
    "brng_put",
    "run_legacy_case",
]

__version__ = "0.1.0"
