"""Defines which functions acquire resources and how they should be released"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ResourcePattern:
    
    name: str  # Human-readable name (e.g., "file", "socket")
    
    # Acquisition patterns: (module, function) or (None, function) for builtins
    acquisitions: List[tuple]
    
    # Release method names (e.g., ["close"])
    release_methods: List[str]
    
    # Does this resource support context managers naturally?
    supports_context_manager: bool = True


# Core resource families we track
RESOURCE_PATTERNS = [
    ResourcePattern(
        name="file",
        acquisitions=[
            (None, "open"),  # built-in open()
            ("io", "open"),
            ("pathlib.Path", "open"),
        ],
        release_methods=["close"],
        supports_context_manager=True,
    ),
    ResourcePattern(
        name="socket",
        acquisitions=[
            ("socket", "socket"),
            ("socket", "create_connection"),
        ],
        release_methods=["close"],
        supports_context_manager=True,
    ),
    ResourcePattern(
        name="database",
        acquisitions=[
            ("sqlite3", "connect"),
        ],
        release_methods=["close"],
        supports_context_manager=True,
    ),
    ResourcePattern(
        name="lock",
        acquisitions=[
            # Note: threading.Lock() creates the lock but doesn't acquire it
            # We track .acquire() calls in the analyzer separately
        ],
        release_methods=["release"],
        supports_context_manager=True,
    ),
]


def get_resource_type(module: Optional[str], func: str) -> Optional[ResourcePattern]:
    for pattern in RESOURCE_PATTERNS:
        for acq_module, acq_func in pattern.acquisitions:
            if acq_module == module and acq_func == func:
                return pattern
    return None


# Configurable whitelist: functions that take ownership of resources
# If a resource is passed to one of these, we assume it's safely handled
OWNERSHIP_TRANSFER_FUNCTIONS = {
    "os.fdopen",  # takes a file descriptor
    "logging.FileHandler",  # takes a file path but manages the file
}
