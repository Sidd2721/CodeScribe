"""
CodeScribe AI - Data Flow Analyzer
====================================
Analyzes how data moves through code using AST-based static analysis.

CORE PRINCIPLE: Deterministic before Generative
- Only uses AST-extracted facts
- No runtime inference
- No variable state guessing
- Explains structure, not execution outcomes
"""

from typing import Dict, Any, List, Set


def analyze_data_flow(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze data flow patterns in the codebase.
    
    Returns:
        Dict with entry_points, processing_stages, coordinators, exit_points
    """
    functions = analysis_data.get('functions', [])
    classes = analysis_data.get('classes', [])
    calls = analysis_data.get('calls', [])
    
    # Get all methods from classes
    all_methods = []
    for cls in classes:
        for method in cls.get('methods', []):
            method_copy = method.copy()
            method_copy['class_name'] = cls['name']
            all_methods.append(method_copy)
    
    # Combine functions and methods for analysis
    all_callable = functions + all_methods
    
    entry_points = _identify_entry_points(all_callable)
    processing_stages = _identify_processing_stages(all_callable, calls)
    coordinators = _identify_coordinators(calls, all_callable)
    exit_points = _identify_exit_points(all_callable)
    
    return {
        'entry_points': entry_points,
        'processing_stages': processing_stages,
        'coordinators': coordinators,
        'exit_points': exit_points,
        'flow_nodes': _build_flow_nodes(entry_points, processing_stages, coordinators, exit_points)
    }


def _identify_entry_points(callables: List[Dict]) -> List[Dict]:
    """
    Identify functions/methods that accept data (have parameters).
    These are potential data entry points.
    """
    entry_points = []
    
    for func in callables:
        args = func.get('args', [])
        name = func.get('name', '')
        
        # Skip special methods except __init__
        if name.startswith('_') and name != '__init__':
            continue
        
        # Functions with parameters are data entry points
        if args:
            class_name = func.get('class_name')
            display_name = f"{class_name}.{name}" if class_name else name
            
            entry_points.append({
                'name': display_name,
                'param_count': len(args),
                'params': args[:3],  # First 3 params
                'type': 'method' if class_name else 'function'
            })
    
    return entry_points[:10]  # Limit to top 10


def _identify_processing_stages(callables: List[Dict], calls: List[Dict]) -> List[Dict]:
    """
    Identify functions/methods that likely process or transform data.
    Heuristics:
    - Has both input (parameters) and output (called by others or returns)
    - Has meaningful name suggesting transformation (process, parse, transform, etc.)
    """
    processing_stages = []
    
    # Build set of functions that are called
    called_funcs = set()
    for call in calls:
        callee = call.get('callee', '')
        if callee:
            called_funcs.add(callee)
    
    for func in callables:
        name = func.get('name', '')
        args = func.get('args', [])
        class_name = func.get('class_name')
        
        # Skip special methods except __init__
        if name.startswith('_') and name != '__init__':
            continue
        
        # Processing heuristics
        is_called = name in called_funcs
        has_input = len(args) > 0
        has_transform_name = any(keyword in name.lower() for keyword in [
            'process', 'parse', 'transform', 'convert', 'analyze', 
            'build', 'generate', 'create', 'compute', 'calculate'
        ])
        
        if (is_called and has_input) or has_transform_name:
            display_name = f"{class_name}.{name}" if class_name else name
            
            processing_stages.append({
                'name': display_name,
                'param_count': len(args),
                'is_called': is_called,
                'suggests_transform': has_transform_name,
                'type': 'method' if class_name else 'function'
            })
    
    return processing_stages[:10]  # Limit to top 10


def _identify_coordinators(calls: List[Dict], callables: List[Dict]) -> List[Dict]:
    """
    Identify components that coordinate/route data flow.
    Heuristics:
    - Makes multiple calls to other functions
    - Acts as orchestrator
    """
    coordinators = []
    
    # Count outgoing calls per function
    call_counts = {}
    for call in calls:
        caller = call.get('caller_scope', '')
        if caller and caller not in ('<module>', 'global'):
            call_counts[caller] = call_counts.get(caller, 0) + 1
    
    # Coordinators make multiple calls
    for caller, count in sorted(call_counts.items(), key=lambda x: x[1], reverse=True):
        if count >= 2:  # Must coordinate at least 2 other components
            coordinators.append({
                'name': caller,
                'outgoing_calls': count,
                'role': 'coordinator'
            })
    
    return coordinators[:8]  # Top 8 coordinators


def _identify_exit_points(callables: List[Dict]) -> List[Dict]:
    """
    Identify where data exits the system.
    Heuristics:
    - Functions that are not called by others (leaf nodes)
    - Functions with names suggesting output (save, write, return, send, etc.)
    """
    exit_points = []
    
    for func in callables:
        name = func.get('name', '')
        class_name = func.get('class_name')
        
        # Skip special methods
        if name.startswith('_') and name != '__init__':
            continue
        
        # Exit point heuristics
        has_exit_name = any(keyword in name.lower() for keyword in [
            'save', 'write', 'send', 'export', 'output', 'print', 
            'store', 'return', 'render', 'display'
        ])
        
        if has_exit_name:
            display_name = f"{class_name}.{name}" if class_name else name
            
            exit_points.append({
                'name': display_name,
                'type': 'method' if class_name else 'function',
                'suggests_output': has_exit_name
            })
    
    return exit_points[:8]  # Limit to top 8


def _build_flow_nodes(entry_points: List[Dict], processing_stages: List[Dict], 
                     coordinators: List[Dict], exit_points: List[Dict]) -> List[Dict]:
    """
    Build a simplified list of flow nodes for diagram generation.
    """
    flow_nodes = []
    
    # Add entry nodes
    for entry in entry_points[:3]:  # Top 3 entries
        flow_nodes.append({
            'id': f"entry_{len(flow_nodes)}",
            'label': entry['name'],
            'shape': 'input',
            'stage': 'entry'
        })
    
    # Add processing nodes
    for processor in processing_stages[:4]:  # Top 4 processors
        flow_nodes.append({
            'id': f"process_{len(flow_nodes)}",
            'label': processor['name'],
            'shape': 'process',
            'stage': 'processing'
        })
    
    # Add coordinator nodes
    for coord in coordinators[:2]:  # Top 2 coordinators
        flow_nodes.append({
            'id': f"coord_{len(flow_nodes)}",
            'label': coord['name'],
            'shape': 'control',
            'stage': 'coordination'
        })
    
    # Add exit nodes
    for exit_pt in exit_points[:2]:  # Top 2 exits
        flow_nodes.append({
            'id': f"exit_{len(flow_nodes)}",
            'label': exit_pt['name'],
            'shape': 'output',
            'stage': 'exit'
        })
    
    return flow_nodes
