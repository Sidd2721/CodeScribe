"""
CodeScribe AI - Mermaid.js Diagram Generator
==============================================
Generates clean, straight Mermaid.js diagrams from AST analysis data.

LAYOUT RULES:
- Strict TB (Top-Bottom) or LR (Left-Right) direction
- No radial or scattered layouts
- Clear hierarchical levels

SHAPE MAPPING:
- {{name}} → Hexagon (entry point)
- [name] → Rectangle (global function)
- ([name]) → Stadium/Rounded (class method)  
- ((name)) → Circle (built-in)
"""

from typing import List, Dict, Any, Set, Tuple
import textwrap


def wrap_label(text: str, max_width: int = 20) -> str:
    """
    Wrap long labels for Mermaid nodes using <br/> for line breaks.
    """
    if len(text) <= max_width:
        return text
    
    # Split at underscores and dots
    parts = text.replace('_', ' ').replace('.', ' ').split()
    lines = []
    current_line = ""
    
    for part in parts:
        if len(current_line) + len(part) + 1 <= max_width:
            current_line = f"{current_line} {part}".strip()
        else:
            if current_line:
                lines.append(current_line)
            current_line = part
    
    if current_line:
        lines.append(current_line)
    
    return "<br/>".join(lines) if lines else text[:max_width]


def sanitize_id(name: str) -> str:
    """
    Create a safe Mermaid node ID from a name.
    """
    return name.replace('.', '_').replace('<', '').replace('>', '').replace(' ', '_')


def categorize_for_mermaid(name: str) -> Tuple[str, int]:
    """
    Categorize a node and return (category, level).
    
    Categories:
    - entry: Entry points (level 0)
    - global: Global functions (level 1)
    - method: Class methods (level 2)
    - builtin: Built-in calls (level 3)
    """
    BUILTINS = {
        'print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict', 'set',
        'tuple', 'bool', 'type', 'isinstance', 'hasattr', 'getattr', 'setattr',
        'open', 'input', 'sorted', 'reversed', 'enumerate', 'zip', 'map', 'filter',
        'sum', 'min', 'max', 'abs', 'round', 'any', 'all', 'format', 'repr', 'super'
    }
    
    if name in ('global', '<module>', 'module', '__main__', 'main'):
        return 'entry', 0
    if name in BUILTINS or name.startswith('__'):
        return 'builtin', 3
    if '.' in name:
        return 'method', 2
    return 'global', 1


def get_mermaid_shape(category: str, node_id: str, label: str) -> str:
    """
    Return Mermaid node definition with appropriate shape.
    
    Shape mapping:
    - entry → hexagon {{}}
    - global → rectangle []
    - method → stadium ([])
    - builtin → circle (())
    """
    shapes = {
        'entry': f'{node_id}{{{{"{label}"}}}}',
        'global': f'{node_id}["{label}"]',
        'method': f'{node_id}(["{label}"])',
        'builtin': f'{node_id}(("{label}"))',
    }
    return shapes.get(category, f'{node_id}["{label}"]')


def generate_call_graph_mermaid(calls: List[Dict[str, Any]]) -> str:
    """
    Generate Mermaid.js call graph with strict TB (top-to-bottom) layout.
    
    Returns a complete Mermaid graph definition string.
    """
    if not calls:
        return """graph TB
    empty["No function calls detected"]
    style empty fill:#2d2d3a,stroke:#666,color:#999"""
    
    lines = ["graph TB"]
    
    # Collect unique nodes and edges
    nodes: Dict[str, Tuple[str, int]] = {}  # name -> (category, level)
    edges: Set[Tuple[str, str]] = set()
    
    for call in calls:
        caller = call.get('caller_scope', 'global')
        callee = call.get('callee', '?')
        
        if caller == callee:
            continue
        
        edges.add((caller, callee))
        
        if caller not in nodes:
            nodes[caller] = categorize_for_mermaid(caller)
        if callee not in nodes:
            nodes[callee] = categorize_for_mermaid(callee)
    
    # Limit for clarity
    if len(nodes) > 15:
        # Keep only the most connected nodes
        edge_count = {}
        for caller, callee in edges:
            edge_count[caller] = edge_count.get(caller, 0) + 1
            edge_count[callee] = edge_count.get(callee, 0) + 1
        
        top_nodes = sorted(edge_count.keys(), key=lambda x: edge_count[x], reverse=True)[:15]
        nodes = {k: v for k, v in nodes.items() if k in top_nodes}
        edges = {(c, e) for c, e in edges if c in top_nodes and e in top_nodes}
    
    # Group nodes by level using subgraphs
    levels: Dict[int, List[str]] = {0: [], 1: [], 2: [], 3: []}
    for name, (category, level) in nodes.items():
        levels[level].append(name)
    
    level_names = {0: "Entry Points", 1: "Core Functions", 2: "Class Methods", 3: "Built-ins"}
    
    # Define nodes within subgraphs for level organization
    for level in sorted(levels.keys()):
        if not levels[level]:
            continue
        
        lines.append(f"    subgraph L{level}[\"{level_names[level]}\"]")
        for name in sorted(levels[level]):
            category, _ = nodes[name]
            node_id = sanitize_id(name)
            label = wrap_label(name, 18)
            node_def = get_mermaid_shape(category, node_id, label)
            lines.append(f"        {node_def}")
        lines.append("    end")
    
    lines.append("")
    
    # Define edges
    for caller, callee in sorted(edges):
        caller_id = sanitize_id(caller)
        callee_id = sanitize_id(callee)
        lines.append(f"    {caller_id} --> {callee_id}")
    
    # Add styling
    lines.append("")
    lines.append("    %% Styling")
    lines.append("    classDef entry fill:#e94560,stroke:#fff,color:#fff")
    lines.append("    classDef global fill:#4ecdc4,stroke:#fff,color:#fff")
    lines.append("    classDef method fill:#45b7d1,stroke:#fff,color:#fff")
    lines.append("    classDef builtin fill:#a29bfe,stroke:#fff,color:#fff")
    
    # Apply classes
    for name, (category, _) in nodes.items():
        node_id = sanitize_id(name)
        lines.append(f"    class {node_id} {category}")
    
    return "\n".join(lines)


def generate_class_diagram_mermaid(classes: List[Dict[str, Any]]) -> str:
    """
    Generate Mermaid.js class diagram.
    Simple boxes with methods listed, no UML symbols.
    """
    if not classes:
        return """graph TB
    empty["No classes defined"]
    style empty fill:#2d2d3a,stroke:#666,color:#999"""
    
    lines = ["classDiagram"]
    
    for cls in classes:
        class_name = cls['name']
        methods = cls.get('methods', [])
        
        # Sort methods: __init__ first
        sorted_methods = sorted(methods, key=lambda m: (
            0 if m['name'] == '__init__' else 1,
            m['name']
        ))
        
        lines.append(f"    class {class_name} {{")
        
        # Limit displayed methods
        for method in sorted_methods[:8]:
            method_name = method['name']
            if len(method_name) > 25:
                method_name = method_name[:22] + "..."
            lines.append(f"        {method_name}()")
        
        if len(sorted_methods) > 8:
            lines.append(f"        ... +{len(sorted_methods) - 8} more")
        
        lines.append("    }")
    
    # Add styling note
    lines.append("")
    lines.append("    %% Clean styling - no UML symbols")
    
    return "\n".join(lines)


def generate_import_graph_mermaid(imports: List[Dict[str, Any]], filename: str) -> str:
    """
    Generate Mermaid.js import dependency graph with LR (left-to-right) layout.
    """
    if not imports:
        return """graph LR
    empty["No imports found"]
    style empty fill:#2d2d3a,stroke:#666,color:#999"""
    
    STDLIB = {
        'os', 'sys', 'json', 'math', 'typing', 'hashlib', 'ast', 're', 
        'datetime', 'collections', 'itertools', 'functools', 'pathlib',
        'random', 'time', 'io', 'copy', 'abc', 'dataclasses', 'logging'
    }
    
    lines = ["graph LR"]
    
    central = filename.replace('.py', '')
    central_id = sanitize_id(central)
    
    # Central node
    lines.append(f'    {central_id}["{central}"]')
    
    stdlib_imports = []
    external_imports = []
    
    for imp in imports:
        module = imp.get('module') or imp.get('name')
        if module:
            base_module = module.split('.')[0]
            if base_module not in [central, central_id]:
                if base_module in STDLIB:
                    if base_module not in stdlib_imports:
                        stdlib_imports.append(base_module)
                else:
                    if base_module not in external_imports:
                        external_imports.append(base_module)
    
    # Subgraphs for organization
    if stdlib_imports:
        lines.append('    subgraph stdlib["Standard Library"]')
        for mod in sorted(stdlib_imports)[:10]:
            mod_id = sanitize_id(mod)
            lines.append(f'        {mod_id}(("{mod}"))')
        lines.append('    end')
    
    if external_imports:
        lines.append('    subgraph external["External Packages"]')
        for mod in sorted(external_imports)[:10]:
            mod_id = sanitize_id(mod)
            lines.append(f'        {mod_id}(["{mod}"])')
        lines.append('    end')
    
    lines.append("")
    
    # Edges
    for mod in stdlib_imports[:10]:
        mod_id = sanitize_id(mod)
        lines.append(f'    {central_id} --> {mod_id}')
    
    for mod in external_imports[:10]:
        mod_id = sanitize_id(mod)
        lines.append(f'    {central_id} --> {mod_id}')
    
    # Styling
    lines.append("")
    lines.append(f"    style {central_id} fill:#e94560,stroke:#fff,color:#fff")
    
    return "\n".join(lines)


def generate_data_flow_diagram(data_flow_analysis: Dict[str, Any]) -> str:
    """
    Generate Mermaid.js data flow structure diagram.
    
    Uses strict top-to-bottom flowchart with shape semantics:
    - Parallelogram [/ /] → Data input
    - Rectangle [ ] → Data processing
    - Rounded rectangle ( ) → Flow control/coordination
    - Oval (( )) → Data output
    
    Args:
        data_flow_analysis: Dict with entry_points, processing_stages, coordinators, exit_points
    
    Returns:
        Mermaid flowchart string
    """
    flow_nodes = data_flow_analysis.get('flow_nodes', [])
    
    if not flow_nodes:
        return """flowchart TD
    empty["No clear data flow detected"]
    style empty fill:#2d2d3a,stroke:#666,color:#999"""
    
    lines = ["flowchart TD"]
    lines.append("    %% Data Flow Structure Diagram")
    lines.append("")
    
    # Group nodes by stage
    entry_nodes = [n for n in flow_nodes if n['stage'] == 'entry']
    process_nodes = [n for n in flow_nodes if n['stage'] == 'processing']
    coord_nodes = [n for n in flow_nodes if n['stage'] == 'coordination']
    exit_nodes = [n for n in flow_nodes if n['stage'] == 'exit']
    
    # Define nodes with shape semantics
    if entry_nodes:
        lines.append("    %% Data Entry Points")
        for node in entry_nodes:
            node_id = sanitize_id(node['id'])
            label = wrap_label(node['label'], 16)
            lines.append(f'    {node_id}[/"{label}"/]')
        lines.append("")
    
    if process_nodes:
        lines.append("    %% Processing Stages")
        for node in process_nodes:
            node_id = sanitize_id(node['id'])
            label = wrap_label(node['label'], 16)
            lines.append(f'    {node_id}["{label}"]')
        lines.append("")
    
    if coord_nodes:
        lines.append("    %% Coordinators")
        for node in coord_nodes:
            node_id = sanitize_id(node['id'])
            label = wrap_label(node['label'], 16)
            lines.append(f'    {node_id}("{label}")')
        lines.append("")
    
    if exit_nodes:
        lines.append("    %% Exit Points")
        for node in exit_nodes:
            node_id = sanitize_id(node['id'])
            label = wrap_label(node['label'], 16)
            lines.append(f'    {node_id}(("{label}"))')
        lines.append("")
    
    # Create linear top-to-bottom flow connections
    lines.append("    %% Flow Connections")
    all_ordered_nodes = entry_nodes + process_nodes + coord_nodes + exit_nodes
    
    for i in range(len(all_ordered_nodes) - 1):
        curr_id = sanitize_id(all_ordered_nodes[i]['id'])
        next_id = sanitize_id(all_ordered_nodes[i + 1]['id'])
        lines.append(f'    {curr_id} --> {next_id}')
    
    # Styling
    lines.append("")
    lines.append("    %% Styling")
    lines.append("    classDef entryClass fill:#4ecdc4,stroke:#fff,stroke-width:2px,color:#fff")
    lines.append("    classDef processClass fill:#45b7d1,stroke:#fff,stroke-width:2px,color:#fff")
    lines.append("    classDef coordClass fill:#bb86fc,stroke:#fff,stroke-width:2px,color:#fff")
    lines.append("    classDef exitClass fill:#e94560,stroke:#fff,stroke-width:2px,color:#fff")
    
    # Apply classes
    for node in entry_nodes:
        lines.append(f'    class {sanitize_id(node["id"])} entryClass')
    for node in process_nodes:
        lines.append(f'    class {sanitize_id(node["id"])} processClass')
    for node in coord_nodes:
        lines.append(f'    class {sanitize_id(node["id"])} coordClass')
    for node in exit_nodes:
        lines.append(f'    class {sanitize_id(node["id"])} exitClass')
    
    return "\n".join(lines)

