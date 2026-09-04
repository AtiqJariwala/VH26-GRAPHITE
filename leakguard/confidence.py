"""Confidence scoring for leak detection findings."""

from enum import Enum


class Confidence(Enum):
    """Confidence level for a resource leak finding."""
    
    DEFINITELY = "definitely"  # No release on any path
    LIKELY = "likely"  # Release on some paths but not all
    POSSIBLE = "possible"  # Ownership unknown / reassigned / passed to unknown function
    
    def __str__(self):
        return self.value
    
    @classmethod
    def from_string(cls, s: str):
        """Parse confidence level from CLI flag."""
        s = s.lower()
        for conf in cls:
            if conf.value == s:
                return conf
        raise ValueError(f"Invalid confidence level: {s}")
    def should_fail(self, threshold: "Confidence") -> bool:
        levels = {
            Confidence.DEFINITELY: 3,
            Confidence.LIKELY: 2,
            Confidence.POSSIBLE: 1,
        }
        return levels[self] >= levels[threshold]
