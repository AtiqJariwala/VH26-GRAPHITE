"""Lightweight control-flow graph for path-sensitive analysis."""

import ast
from dataclasses import dataclass, field
from typing import Set, Optional, List
from enum import Enum


class PathStatus(Enum):
    UNKNOWN = "unknown"  # Haven't analyzed yet
    OPEN = "open"  # Resource is still open on this path
    CLOSED = "closed"  # Resource was explicitly closed
    CONTEXT_MANAGED = "context_managed"  # Inside a 'with' statement
    OWNERSHIP_TRANSFERRED = "ownership_transferred"  # Passed to a function that takes ownership
    OWNERSHIP_UNKNOWN = "ownership_unknown"  # Passed to unknown function or reassigned


@dataclass
class ResourceState:

    var_name: str  # Variable holding the resource
    resource_type: str  # "file", "socket", etc.
    acquisition_line: int
    acquisition_expr: str  # The actual code expression
    
   
    path_states: dict = field(default_factory=lambda: {"default": PathStatus.OPEN})
    
    reassigned: bool = False
    
    in_context_manager: bool = False
    
    passed_to_function: Optional[str] = None
    
    def mark_closed(self, path="default"):
        self.path_states[path] = PathStatus.CLOSED
    
    def mark_context_managed(self):
        self.in_context_manager = True
        for path in self.path_states:
            self.path_states[path] = PathStatus.CONTEXT_MANAGED
    
    def mark_transferred(self, func_name: str):
        self.passed_to_function = func_name
        for path in self.path_states:
            self.path_states[path] = PathStatus.OWNERSHIP_TRANSFERRED
    
    def mark_ownership_unknown(self, reason: str):
        self.passed_to_function = reason
        for path in self.path_states:
            self.path_states[path] = PathStatus.OWNERSHIP_UNKNOWN
    
    def is_leaked(self) -> tuple[bool, str]:
        # Safe cases
        if self.in_context_manager:
            return False, "context_managed", "used in context manager"
        
        if PathStatus.OWNERSHIP_TRANSFERRED in self.path_states.values():
            return False, "transferred", "ownership transferred to safe function"
        
        # Warning cases
        if self.reassigned:
            return True, "possible", f"variable '{self.var_name}' was reassigned, unclear if original resource was closed"
        
        if PathStatus.OWNERSHIP_UNKNOWN in self.path_states.values():
            return True, "possible", f"resource passed to function '{self.passed_to_function}', ownership unclear"
        
        # Check path states
        open_paths = [p for p, status in self.path_states.items() if status == PathStatus.OPEN]
        closed_paths = [p for p, status in self.path_states.items() if status == PathStatus.CLOSED]
        
        if not closed_paths:
            # No close() found on any path
            return True, "definitely", f"no close() found on any execution path"
        
        if open_paths:
            # Close found on some paths but not all
            paths_desc = ", ".join(open_paths)
            return True, "likely", f"no close() found on path(s): {paths_desc}"
        
        # All paths have close()
        return False, "safe", "closed on all paths"


class ControlFlowTracker:
    
    def __init__(self):
        self.resources: List[ResourceState] = []  # All resources tracked
        self.current_path = "default"
        self.in_try_block = False
        self.in_finally_block = False
        self.finally_closes = set()  # Resources closed in finally blocks
        self._var_to_resource: dict[str, ResourceState] = {}  # Current var -> resource mapping
    
    def acquire_resource(self, var_name: str, resource_type: str, line: int, expr: str):
    
        if var_name in self._var_to_resource:
            self._var_to_resource[var_name].reassigned = True
        
        new_resource = ResourceState(
            var_name=var_name,
            resource_type=resource_type,
            acquisition_line=line,
            acquisition_expr=expr,
        )
        self.resources.append(new_resource)
        self._var_to_resource[var_name] = new_resource
    
    def release_resource(self, var_name: str):
        if var_name in self._var_to_resource:
            resource = self._var_to_resource[var_name]
            # If closed in finally, it's closed on all paths
            if self.in_finally_block:
                self.finally_closes.add(var_name)
                # Mark closed on all paths
                for path in list(resource.path_states.keys()):
                    resource.mark_closed(path)
            else:
                resource.mark_closed(self.current_path)
    
    def mark_context_managed(self, var_name: str):
        if var_name in self._var_to_resource:
            self._var_to_resource[var_name].mark_context_managed()
    
    def mark_reassigned(self, var_name: str):
        if var_name in self._var_to_resource:
            self._var_to_resource[var_name].reassigned = True
    
    def mark_passed_to_function(self, var_name: str, func_name: str, is_safe: bool):
        if var_name in self._var_to_resource:
            resource = self._var_to_resource[var_name]
            if is_safe:
                resource.mark_transferred(func_name)
            else:
                resource.mark_ownership_unknown(func_name)
    
    def enter_branch(self, branch_name: str):
       
        self.current_path = branch_name
        for resource in self.resources:
            if branch_name not in resource.path_states:
                resource.path_states[branch_name] = PathStatus.OPEN
    
    def get_leaked_resources(self) -> List[ResourceState]:
        leaked = []
        for resource in self.resources:
            is_leak, confidence, explanation = resource.is_leaked()
            if is_leak:
                leaked.append(resource)
        return leaked
