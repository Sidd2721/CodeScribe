import ast
import json
from typing import Dict, List, Any, Optional

class CodeVisitor(ast.NodeVisitor):
    def __init__(self):
        self.structure = {
            "classes": [],
            "functions": [],
            "imports": [],
            "calls": []
        }
        self.current_scope = ["global"]
        self.current_class = None

    def visit_Import(self, node):
        for alias in node.names:
            self.structure["imports"].append({"name": alias.name, "asname": alias.asname})
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ""
        for alias in node.names:
            self.structure["imports"].append({"module": module, "name": alias.name, "asname": alias.asname})
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        class_info = {
            "name": node.name,
            "bases": [b.id if isinstance(b, ast.Name) else str(b) for b in node.bases],
            "docstring": ast.get_docstring(node),
            "methods": [],
            "start_line": node.lineno,
            "end_line": node.end_lineno
        }
        
        # Track current class context
        previous_class = self.current_class
        self.current_class = class_info
        self.current_scope.append(node.name)
        
        # Visit body to process methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self.visit(item)
        
        self.structure["classes"].append(class_info)
        
        # Restore context
        self.current_scope.pop()
        self.current_class = previous_class

    def visit_FunctionDef(self, node):
        func_info = {
            "name": node.name,
            "args": [arg.arg for arg in node.args.args],
            "docstring": ast.get_docstring(node),
            "calls": [],
            "start_line": node.lineno,
            "end_line": node.end_lineno,
            "scope": ".".join(self.current_scope)
        }
        
        # Track current function context for calls
        start_calls_len = len(self.structure["calls"])
        self.current_scope.append(node.name)
        
        self.generic_visit(node)
        
        # Collect calls made within this function
        # Note: In a real implementation we might want to attach calls directly to the function object.
        # But for now, we leave them in the global 'calls' list or filter them.
        # Let's actually add them to the function info for better locality in the JSON.
        # But since generic_visit visits children, checking calls after visit is tricky unless we track them.
        # For simplicity in this 'fact sheet', we can just use the global tracking of calls
        # with the 'scope' attribute to link them back.
        
        self.current_scope.pop()

        if self.current_class:
            self.current_class["methods"].append(func_info)
        else:
            self.structure["functions"].append(func_info)

    def visit_Call(self, node):
        # Extract function being called
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            # Helper to get full attribute path e.g. self.method or module.func
            parts = []
            curr = node.func
            while isinstance(curr, ast.Attribute):
                parts.append(curr.attr)
                curr = curr.value
            if isinstance(curr, ast.Name):
                parts.append(curr.id)
            func_name = ".".join(reversed(parts))
        
        if func_name:
            call_info = {
                "caller_scope": ".".join(self.current_scope),
                "callee": func_name,
                "line": node.lineno
            }
            self.structure["calls"].append(call_info)
        
        self.generic_visit(node)

def analyze_code(source_code: str) -> Dict[str, Any]:
    """
    Parses Python source code and returns a dictionary representing its structure
    (classes, functions, imports, function calls).
    """
    try:
        tree = ast.parse(source_code)
        visitor = CodeVisitor()
        visitor.visit(tree)
        return visitor.structure
    except SyntaxError as e:
        return {"error": f"SyntaxError: {e}"}
    except Exception as e:
        return {"error": f"Error parsing code: {e}"}
