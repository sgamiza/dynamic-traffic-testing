"""Offline-testable business logic extracted from the lab DDTT toolkit.

The original lab modules under ``l3_ddtt_tool`` stay intact for hardware
runs. This package is the resume-grade, hardware-free layer used by unit tests.
"""

from .config import DdttConfigError, load_ddtt_config, validate_ddtt_config
from .judgment import POWER_MARGIN_DB, power_exceeds_pmax, query_powers_above_pmax
from .profiles import enabled_profiles, sequence_duration_minutes
from .results_db import ResultsDB
from .ue_identity import validate_ue_identity

__all__ = [
    "DdttConfigError",
    "POWER_MARGIN_DB",
    "ResultsDB",
    "enabled_profiles",
    "load_ddtt_config",
    "power_exceeds_pmax",
    "query_powers_above_pmax",
    "sequence_duration_minutes",
    "validate_ddtt_config",
    "validate_ue_identity",
]
