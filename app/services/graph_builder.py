"""
CodeScribe AI - Professional Visualization System
===================================================
CORE PRINCIPLE: Visual Clarity + Shape = Meaning

SHAPE MAPPING:
- Hexagon (⬡) → Entry points (main, module-level)
- Rectangle (□) → Global/top-level functions  
- Rounded Rectangle (▢) → Class methods
- Circle (○) → Built-in/external calls

LAYOUT: Strict hierarchical Top-to-Bottom (TB) or Left-to-Right (LR)
NO radial, scattered, or free-form layouts.
"""

import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from typing import List, Dict, Any, Tuple, Set
import os
import hashlib
import textwrap


# Built-in functions list
BUILTINS = {
    'print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict', 'set',
    'tuple', 'bool', 'type', 'isinstance', 'hasattr', 'getattr', 'setattr',
    'open', 'input', 'sorted', 'reversed', 'enumerate', 'zip', 'map', 'filter',
    'sum', 'min', 'max', 'abs', 'round', 'any', 'all', 'format', 'repr',
    'super', 'property', 'classmethod', 'staticmethod', 'vars', 'dir', 'id',
    'hash', 'callable', 'iter', 'next', 'slice', 'object', 'exec', 'eval'
}


def wrap_text(text: str, max_width: int = 18) -> str:
    """
    Wrap long text for node labels to prevent overflow.
    Splits at underscores, dots, and camelCase boundaries.
    """
    if len(text) <= max_width:
        return text
    
    # Replace underscores and dots with spaces for wrapping
    wrapped = text.replace('_', '_\n').replace('.', '.\n')
    if len(wrapped) > len(text):
        # Clean up excessive newlines
        lines = [l.strip() for l in wrapped.split('\n') if l.strip()]
        result_lines = []
        current = ""
        for line in lines:
            if len(current) + len(line) <= max_width:
                current += line
            else:
                if current:
                    result_lines.append(current)
                current = line
        if current:
            result_lines.append(current)
        return '\n'.join(result_lines)
    
    # Fallback: hard wrap
    return '\n'.join(textwrap.wrap(text, width=max_width))


def categorize_node(name: str, is_caller: bool = False) -> Tuple[str, int]:
    """
    Categorize a node by its type based on AST-extracted name.
    Returns: (category, level) where level is used for hierarchical placement.
    
    Levels (top to bottom):
    - 0: Entry points (highest)
    - 1: Global functions
    - 2: Class methods
    - 3: Built-ins/external (lowest)
    """
    if name in ('global', '<module>', 'module', '__main__', 'main'):
        return 'entry', 0
    if name in BUILTINS or name.startswith('__'):
        return 'builtin', 3
    if '.' in name:
        return 'method', 2
    if name[0].isupper():
        return 'class', 1
    return 'global', 1


def get_node_style(category: str) -> Dict[str, Any]:
    """
    Return visual style for each node category.
    SHAPE = MEANING principle applied consistently.
    """
    styles = {
        'entry': {
            'color': '#e94560',      # Red - attention
            'shape': 'h',            # Hexagon
            'size': 4000,
            'label': 'Entry Point'
        },
        'global': {
            'color': '#4ecdc4',      # Teal
            'shape': 's',            # Square/Rectangle
            'size': 3200,
            'label': 'Global Function'
        },
        'method': {
            'color': '#45b7d1',      # Blue
            'shape': 'o',            # Circle (represents rounded rect concept)
            'size': 2800,
            'label': 'Class Method'
        },
        'builtin': {
            'color': '#a29bfe',      # Purple
            'shape': 'o',            # Circle
            'size': 2200,
            'label': 'Built-in Call'
        },
        'class': {
            'color': '#f9ca24',      # Yellow
            'shape': 'd',            # Diamond
            'size': 3200,
            'label': 'Class'
        }
    }
    return styles.get(category, styles['global'])


def compute_hierarchical_layout(G: nx.DiGraph, node_levels: Dict[str, int]) -> Dict[str, Tuple[float, float]]:
    """
    Compute a strict hierarchical top-to-bottom layout.
    Nodes are positioned in horizontal layers based on their level.
    """
    # Group nodes by level
    levels: Dict[int, List[str]] = {}
    for node, level in node_levels.items():
        if node in G.nodes():
            if level not in levels:
                levels[level] = []
            levels[level].append(node)
    
    if not levels:
        return {}
    
    pos = {}
    sorted_levels = sorted(levels.keys())
    num_levels = len(sorted_levels)
    
    # Vertical spacing between levels
    y_step = 1.0 / max(num_levels, 1)
    
    for level_idx, level in enumerate(sorted_levels):
        nodes = levels[level]
        num_nodes = len(nodes)
        
        # Y position: higher levels at top (inverted)
        y = 1.0 - (level_idx + 0.5) * y_step
        
        # X positions: distribute horizontally with even spacing
        for node_idx, node in enumerate(sorted(nodes)):
            if num_nodes == 1:
                x = 0.5
            else:
                x = (node_idx + 0.5) / num_nodes
            pos[node] = (x, y)
    
    return pos


def generate_call_graph(calls: List[Dict[str, Any]], filename: str) -> str:
    """
    Generate a hierarchical call graph with strict TB (top-to-bottom) layout.
    
    VISUAL RULES:
    - Different shapes = different entity types
    - Entry points at top (level 0)
    - Execution flows downward
    - No radial or scattered layouts
    - Text contained within nodes via wrapping
    """
    G = nx.DiGraph()
    node_categories = {}
    node_levels = {}
    
    # Deduplicate and categorize
    seen: Set[Tuple[str, str]] = set()
    for call in calls:
        caller = call.get('caller_scope', 'global')
        callee = call.get('callee', '?')
        
        if caller == callee or (caller, callee) in seen:
            continue
        seen.add((caller, callee))
        
        G.add_edge(caller, callee)
        
        cat, lvl = categorize_node(caller, is_caller=True)
        node_categories[caller] = cat
        node_levels[caller] = lvl
        
        cat, lvl = categorize_node(callee)
        node_categories[callee] = cat
        node_levels[callee] = lvl
    
    if len(G.nodes()) == 0:
        G.add_node("No calls detected")
        node_categories["No calls detected"] = 'global'
        node_levels["No calls detected"] = 1
    
    # Limit nodes for clarity (keep most connected)
    if len(G.nodes()) > 15:
        degrees = dict(G.degree())
        top = sorted(degrees.keys(), key=lambda x: degrees[x], reverse=True)[:15]
        G = G.subgraph(top).copy()
        node_categories = {k: v for k, v in node_categories.items() if k in G.nodes()}
        node_levels = {k: v for k, v in node_levels.items() if k in G.nodes()}
    
    # Generate filename
    file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
    graph_filename = f"call_graph_{file_hash}.png"
    graph_path = os.path.join("app", "static", "graphs", graph_filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(graph_path), exist_ok=True)
    
    # Create figure with professional styling
    fig, ax = plt.subplots(figsize=(16, 12))
    fig.patch.set_facecolor('#0f0f1a')
    ax.set_facecolor('#0f0f1a')
    
    # Compute hierarchical layout
    pos = compute_hierarchical_layout(G, node_levels)
    
    # Scale positions for better spacing
    scaled_pos = {k: (v[0] * 8 - 4, v[1] * 6 - 3) for k, v in pos.items()}
    
    # Draw nodes by category for shape differentiation
    for category in ['entry', 'global', 'method', 'builtin', 'class']:
        nodes = [n for n in G.nodes() if node_categories.get(n) == category]
        if not nodes:
            continue
        
        style = get_node_style(category)
        nx.draw_networkx_nodes(
            G, scaled_pos, ax=ax,
            nodelist=nodes,
            node_color=style['color'],
            node_size=style['size'],
            node_shape=style['shape'],
            edgecolors='white',
            linewidths=2.5,
            alpha=0.95
        )
    
    # Draw edges with clean vertical arrows (minimize diagonal)
    nx.draw_networkx_edges(
        G, scaled_pos, ax=ax,
        edge_color='#e94560',
        arrows=True,
        arrowsize=20,
        width=2.0,
        alpha=0.75,
        style='solid',
        min_source_margin=30,
        min_target_margin=30,
        connectionstyle='arc3,rad=0.1'
    )
    
    # Prepare wrapped labels
    wrapped_labels = {node: wrap_text(node, 16) for node in G.nodes()}
    
    # Draw labels with proper sizing
    nx.draw_networkx_labels(
        G, scaled_pos, ax=ax,
        labels=wrapped_labels,
        font_size=8,
        font_weight='bold',
        font_color='white',
        verticalalignment='center'
    )
    
    # Legend with shape meanings
    legend_items = [
        mpatches.Patch(color='#e94560', label='⬡ Entry Point'),
        mpatches.Patch(color='#4ecdc4', label='□ Global Function'),
        mpatches.Patch(color='#45b7d1', label='○ Class Method'),
        mpatches.Patch(color='#a29bfe', label='○ Built-in Call'),
        mpatches.Patch(color='#f9ca24', label='◇ Class'),
    ]
    ax.legend(handles=legend_items, loc='upper left',
              facecolor='#1a1a2e', edgecolor='#333',
              labelcolor='white', fontsize=9, framealpha=0.95)
    
    # Title
    ax.set_title(f"Call Graph: {filename}", fontsize=14, fontweight='bold', 
                 color='white', pad=20)
    ax.axis('off')
    
    # Add margin
    ax.margins(0.15)
    
    plt.tight_layout()
    plt.savefig(graph_path, dpi=150, bbox_inches='tight', facecolor='#0f0f1a')
    plt.close()
    
    return f"/static/graphs/{graph_filename}"


def generate_class_diagram(classes: List[Dict[str, Any]], filename: str) -> str:
    """
    Generate a clean, column-based class diagram.
    
    RULES:
    - Vertical column layout with fixed-width containers
    - Class name centered and dominant
    - __init__() always listed first
    - Methods as simple text list
    - No assumed relationships
    - No UML symbols (+, -, #)
    """
    if not classes:
        return ""
    
    file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
    diagram_filename = f"class_diagram_{file_hash}.png"
    diagram_path = os.path.join("app", "static", "graphs", diagram_filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(diagram_path), exist_ok=True)
    
    # Layout calculations
    num_classes = len(classes)
    cols = min(3, num_classes)
    rows = (num_classes + cols - 1) // cols
    
    # Figure dimensions
    fig_width = max(14, cols * 5)
    fig_height = max(8, rows * 5)
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.set_facecolor('#0f0f1a')
    fig.patch.set_facecolor('#0f0f1a')
    
    # Card dimensions
    card_width = 0.28
    col_spacing = 0.32
    row_spacing = 0.45
    
    for idx, cls in enumerate(classes):
        col = idx % cols
        row = idx // cols
        
        # Center position of card
        x = 0.18 + (col * col_spacing)
        y_top = 0.90 - (row * row_spacing)
        
        # Sort methods: __init__ first, then alphabetically
        methods = cls.get('methods', [])
        sorted_methods = sorted(methods, key=lambda m: (
            0 if m['name'] == '__init__' else 1,
            m['name']
        ))
        
        # Limit displayed methods
        display_methods = sorted_methods[:6]
        num_methods = len(display_methods)
        extra_methods = len(sorted_methods) - num_methods
        
        # Card height based on content
        base_height = 0.08
        method_height = 0.035
        card_height = base_height + (num_methods * method_height)
        if extra_methods > 0:
            card_height += 0.03
        
        y_bottom = y_top - card_height
        
        # Main card (rounded rectangle) with clean border
        card = FancyBboxPatch(
            (x - card_width/2, y_bottom),
            card_width, card_height,
            boxstyle="round,pad=0.015,rounding_size=0.02",
            facecolor='#1a1a2e',
            edgecolor='#4ecdc4',
            linewidth=2.5,
            transform=ax.transAxes
        )
        ax.add_patch(card)
        
        # Class name header (bold, prominent, centered)
        class_name = cls['name']
        if len(class_name) > 20:
            class_name = class_name[:17] + '...'
        
        ax.text(x, y_top - 0.025, class_name, transform=ax.transAxes,
                fontsize=13, fontweight='bold', color='#4ecdc4',
                ha='center', va='top', family='sans-serif')
        
        # Separator line
        sep_y = y_top - 0.05
        ax.plot([x - card_width/2 + 0.01, x + card_width/2 - 0.01], 
                [sep_y, sep_y], 
                color='#4ecdc4', alpha=0.4, linewidth=1.5, transform=ax.transAxes)
        
        # Methods (simple text, no UML symbols)
        method_start_y = sep_y - 0.025
        for m_idx, method in enumerate(display_methods):
            method_y = method_start_y - (m_idx * method_height)
            
            # Truncate long method names
            method_name = method['name']
            if len(method_name) > 22:
                method_name = method_name[:19] + '...'
            
            ax.text(x, method_y, f"{method_name}()", 
                    transform=ax.transAxes, fontsize=10, color='#e0e0e0',
                    ha='center', va='top', family='monospace')
        
        # "More" indicator
        if extra_methods > 0:
            more_y = method_start_y - (num_methods * method_height)
            ax.text(x, more_y, f"... +{extra_methods} more",
                    transform=ax.transAxes, fontsize=8, color='#666',
                    ha='center', va='top', style='italic')
    
    ax.set_title(f"Class Diagram: {filename}", fontsize=14, fontweight='bold', 
                 color='white', pad=20)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(diagram_path, dpi=150, bbox_inches='tight', facecolor='#0f0f1a')
    plt.close()
    
    return f"/static/graphs/{diagram_filename}"


def generate_import_graph(imports: List[Dict[str, Any]], filename: str) -> str:
    """
    Generate a Left-to-Right import dependency graph.
    
    LAYOUT:
    - Your file on the LEFT
    - Standard library in MIDDLE column
    - External packages on RIGHT column
    - Clean horizontal flow
    """
    if not imports:
        return ""
    
    file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
    graph_filename = f"import_graph_{file_hash}.png"
    graph_path = os.path.join("app", "static", "graphs", graph_filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(graph_path), exist_ok=True)
    
    G = nx.DiGraph()
    
    # Central node (your file)
    central = filename.replace('.py', '')
    G.add_node(central)
    
    # Standard library modules (expanded list)
    stdlib = {
        'os', 'sys', 'json', 'math', 'typing', 'hashlib', 'ast', 're', 
        'datetime', 'collections', 'itertools', 'functools', 'pathlib',
        'random', 'time', 'io', 'copy', 'abc', 'dataclasses', 'logging',
        'unittest', 'argparse', 'subprocess', 'threading', 'multiprocessing',
        'socket', 'http', 'urllib', 'email', 'html', 'xml', 'sqlite3',
        'csv', 'pickle', 'shelve', 'struct', 'codecs', 'string', 'textwrap',
        'unicodedata', 'locale', 'calendar', 'heapq', 'bisect', 'array',
        'weakref', 'types', 'contextlib', 'inspect', 'dis', 'traceback',
        'warnings', 'errno', 'signal', 'tempfile', 'shutil', 'glob',
        'fnmatch', 'linecache', 'platform', 'secrets', 'statistics'
    }
    
    # Track module types for column positioning
    module_types = {central: 'central'}
    stdlib_nodes = []
    external_nodes = []
    
    for imp in imports:
        module = imp.get('module') or imp.get('name')
        if module:
            base_module = module.split('.')[0]
            if base_module not in G.nodes() and base_module != central:
                G.add_edge(central, base_module)
                if base_module in stdlib:
                    module_types[base_module] = 'stdlib'
                    stdlib_nodes.append(base_module)
                else:
                    module_types[base_module] = 'external'
                    external_nodes.append(base_module)
    
    # If no imports found
    if len(G.nodes()) == 1:
        return ""
    
    # Compute LR column-based layout
    pos = {}
    
    # Central file on left
    pos[central] = (0, 0)
    
    # Stdlib in middle column
    for i, node in enumerate(sorted(stdlib_nodes)):
        y = (i - len(stdlib_nodes)/2) * 0.8
        pos[node] = (2, y)
    
    # External on right column
    for i, node in enumerate(sorted(external_nodes)):
        y = (i - len(external_nodes)/2) * 0.8
        pos[node] = (4, y)
    
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_facecolor('#0f0f1a')
    fig.patch.set_facecolor('#0f0f1a')
    
    # Draw nodes by type with consistent sizing
    # Central (your file)
    if central in pos:
        nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=[central],
                               node_color='#e94560', node_size=4500,
                               node_shape='s',
                               edgecolors='white', linewidths=2.5, alpha=0.95)
    
    # Stdlib nodes
    if stdlib_nodes:
        nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=stdlib_nodes,
                               node_color='#a29bfe', node_size=2500,
                               node_shape='o',
                               edgecolors='white', linewidths=2, alpha=0.95)
    
    # External nodes
    if external_nodes:
        nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=external_nodes,
                               node_color='#4ecdc4', node_size=2500,
                               node_shape='o',
                               edgecolors='white', linewidths=2, alpha=0.95)
    
    # Draw edges with horizontal flow
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color='#bb86fc',
                           arrows=True, arrowsize=20, width=2.0, alpha=0.75,
                           connectionstyle='arc3,rad=0.05')
    
    # Wrapped labels
    wrapped_labels = {node: wrap_text(node, 14) for node in G.nodes()}
    
    # Labels
    nx.draw_networkx_labels(G, pos, ax=ax, labels=wrapped_labels,
                            font_size=9, font_weight='bold', font_color='white')
    
    # Legend
    legend_items = [
        mpatches.Patch(color='#e94560', label='Your File'),
        mpatches.Patch(color='#a29bfe', label='Standard Library'),
        mpatches.Patch(color='#4ecdc4', label='External Package'),
    ]
    ax.legend(handles=legend_items, loc='upper left',
              facecolor='#1a1a2e', edgecolor='#333',
              labelcolor='white', fontsize=9, framealpha=0.95)
    
    ax.set_title(f"Import Dependencies: {filename}", fontsize=14, 
                 fontweight='bold', color='white', pad=20)
    ax.axis('off')
    ax.margins(0.2)
    
    plt.tight_layout()
    plt.savefig(graph_path, dpi=150, bbox_inches='tight', facecolor='#0f0f1a')
    plt.close()
    
    return f"/static/graphs/{graph_filename}"
