"""
Signal generation module for supply chain risk mapper.
This module works with risk_heuristics to generate standardized risk signal entries.
"""

class SignalGenerator:
    def __init__(self):
        pass

    @staticmethod
    def create_signal(signal_type, file_path, line_number=None, detail="", severity="medium"):
        """
        Create a standardized signal entry
        """
        return {
            "type": signal_type,
            "file": file_path,
            "line": line_number,
            "detail": detail,
            "severity": severity
        }

    @staticmethod
    def aggregate_signals(risk_signals):
        """
        Aggregate and potentially deduplicate signals
        """
        # For now, just return the signals as is
        # In the future, we could add deduplication logic here
        return risk_signals