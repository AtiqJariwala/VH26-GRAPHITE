"""AST-based resource leak analyzer.
"""

import ast
from pathlib import Path
from typing import List, Optional

from .cfg import ControlFlowTracker, ResourceState
from .confidence import Confidence
from .report import LeakFinding
from .resources import get_resource_type, OWNERSHIP_TRANSFER_FUNCTIONS


class ResourceAnalyzer(ast.NodeVisitor):

    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.tracker = ControlFlowTracker()
        
        self.context_managed_vars = set()
        
        self.in_function_depth = 0
    
    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                if var_name in self.tracker._var_to_resource and not self.tracker._var_to_resource[var_name].in_context_manager:
                    self.tracker.mark_reassigned(var_name)
        
        if isinstance(node.value, ast.Call):
            func_name, module_name = self._get_function_name(node.value.func)
            
            if func_name:
                resource_type = get_resource_type(module_name, func_name)
                
                if resource_type:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id
                            expr = ast.unparse(node.value)
                            self.tracker.acquire_resource(
                                var_name,
                                resource_type.name,
                                node.lineno,
                                expr
                            )
        
        self.generic_visit(node)
    
    def visit_With(self, node: ast.With):
        for item in node.items:
            if item.optional_vars:
                if isinstance(item.optional_vars, ast.Name):
                    var_name = item.optional_vars.id
                    self.context_managed_vars.add(var_name)
                    self.tracker.mark_context_managed(var_name)
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        # Check if this is a .close() or .release() call
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ("close", "release"):
                # Release call
                if isinstance(node.func.value, ast.Name):
                    var_name = node.func.value.id
                    self.tracker.release_resource(var_name)
            elif node.func.attr == "acquire":
                #Lock .acquire() call - track as resource acquisition
                if isinstance(node.func.value, ast.Name):
                    var_name = node.func.value.id
                    expr = ast.unparse(node)
                    self.tracker.acquire_resource(
                        var_name,
                        "lock",
                        node.lineno,
                        expr
                    )
        
        func_name, _ = self._get_function_name(node.func)
        if func_name:
            full_func_name = self._get_full_function_name(node.func)
            for arg in node.args:
                if isinstance(arg, ast.Name):
                    var_name = arg.id
                    if var_name in self.tracker._var_to_resource:
                        is_safe = full_func_name in OWNERSHIP_TRANSFER_FUNCTIONS
                        self.tracker.mark_passed_to_function(var_name, full_func_name, is_safe)
        
        self.generic_visit(node)
    
    def visit_Return(self, node: ast.Return):
        """Track early returns - resources not closed before return are leaked."""
        # Mark all currently open resources as potentially leaked on this path
        self.tracker.mark_early_return(self.tracker.current_path)
        self.generic_visit(node)
    
    def visit_If(self, node: ast.If):
        """If/else branching."""
        saved_path = self.tracker.current_path
        
        self.visit(node.test)
        
        self.tracker.enter_branch("if_branch")
        for stmt in node.body:
            self.visit(stmt)
        

        if node.orelse:
            self.tracker.enter_branch("else_branch")
            for stmt in node.orelse:
                self.visit(stmt)
        
        self.tracker.current_path = saved_path
    
    def visit_Try(self, node: ast.Try):
        """Handle try/except/finally blocks with proper path tracking."""
        saved_path = self.tracker.current_path
        
        # Track resources closed in finally block separately
        resources_before_finally = set(self.tracker._var_to_resource.keys())
        
        # Visit try block
        self.tracker.in_try_block = True
        self.tracker.enter_branch("try_body")
        for stmt in node.body:
            self.visit(stmt)
        self.tracker.in_try_block = False
               
        # Visit exception handlers
        for handler in node.handlers:
            handler_name = f"except_{handler.type.id if handler.type else 'all'}"
            self.tracker.enter_branch(handler_name)
            for stmt in handler.body:
                self.visit(stmt)
        
        # Visit finally block - resources closed here are closed on ALL paths
        if node.finalbody:        
            self.tracker.in_finally_block = True
            for stmt in node.finalbody:
                self.visit(stmt)
            self.tracker.in_finally_block = False
        
        # Visit else block (only runs if no exception)
        if node.orelse:
            self.tracker.enter_branch("try_else")
            for stmt in node.orelse:
                self.visit(stmt)
        
        self.tracker.current_path = saved_path
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.in_function_depth += 1
        self.generic_visit(node)
        self.in_function_depth -= 1
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.in_function_depth += 1
        self.generic_visit(node)
        self.in_function_depth -= 1
    
    def _get_function_name(self, node) -> tuple[Optional[str], Optional[str]]:
       
        if isinstance(node, ast.Name):

            return node.id, None
        
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                return node.attr, node.value.id
            if isinstance(node.value, ast.Attribute):
                module_parts = []
                current = node.value
                while isinstance(current, ast.Attribute):
                    module_parts.insert(0, current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    module_parts.insert(0, current.id)
                return node.attr, ".".join(module_parts)
        
        return None, None
    
    def _get_full_function_name(self, node) -> str:
       
        if isinstance(node, ast.Name):
            return node.id
        
        if isinstance(node, ast.Attribute):
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.insert(0, current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.insert(0, current.id)
            return ".".join(parts)
        
        return "unknown"
    
    def get_findings(self) -> List[LeakFinding]:
        findings = []
        
        for resource in self.tracker.get_leaked_resources():
            is_leak, confidence_str, explanation = resource.is_leaked()
            
            if is_leak:
                if confidence_str == "definitely":
                    confidence = Confidence.DEFINITELY
                elif confidence_str == "likely":
                    confidence = Confidence.LIKELY
                else:
                    confidence = Confidence.POSSIBLE
                
                finding = LeakFinding(
                    file_path=self.file_path,
                    acquisition_line=resource.acquisition_line,
                    resource_type=resource.resource_type,
                    resource_expr=resource.acquisition_expr,
                    confidence=confidence,
                    explanation=explanation
                )
                findings.append(finding)
        
        return findings


def analyze_file(file_path: Path) -> List[LeakFinding]:
   

    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    
    # Parse the file
    tree = ast.parse(source, filename=str(file_path))
    
    # Analyze
    analyzer = ResourceAnalyzer(str(file_path))
    analyzer.visit(tree)
    
    return analyzer.get_findings()
