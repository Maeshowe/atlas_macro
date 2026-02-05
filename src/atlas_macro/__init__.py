"""
ATLAS MACRO - Macro-Level Market Constraint & Stress Diagnostic

ATLAS answers one question only:
"Are there macro-level conditions that constrain or override
otherwise valid market participation and allocation signals?"

Design Principles:
- Macro is a constraint, not a driver
- No economic forecasting
- No soft data (PMI, CPI, NFP, speeches)
- No narratives
- Deterministic, rule-based
- Discrete states only (CALM / STRESSED / CRISIS)
"""

__version__ = "1.0.0"
