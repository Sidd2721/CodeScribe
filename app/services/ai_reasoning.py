"""
CodeScribe AI - Deep Reasoning Engine
=======================================
Provides intellectually rigorous, structured analysis of code architecture.

REASONING PRINCIPLES:
- Chain of Logic: Observation → Interpretation → Implication
- Every claim must be traceable to AST facts
- No speculation on runtime behavior
- Depth through insight, not length

TARGET AUDIENCE: Technical reviewers, judges, developers
GOAL: Enable 5-7 minute confident explanation of codebase structure
"""

import os
from typing import Dict, Any, List, Tuple
from dotenv import load_dotenv

load_dotenv()


def get_deep_reasoning(analysis_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """
    Generate deep, structured reasoning about code architecture.
    
    Returns comprehensive analysis in 5 layers + graph-specific reasoning.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key or api_key == "your_gemini_api_key_here":
        return _generate_structured_fallback(analysis_data, filename)
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Prepare detailed analysis summary
        summary = _prepare_detailed_analysis(analysis_data, filename)
        
        prompt = f"""You are a software architect analyzing code structure using static analysis data.
Your task is to provide deep, structured reasoning about the codebase architecture.

ANALYSIS DATA (from AST static analysis):
{summary}

YOUR TASK:
Provide structured reasoning following this EXACT format. Be specific and reference actual names from the data.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. ANALYSIS SCOPE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What was analyzed:
[State: file name, number of classes, functions, imports found]

What was extracted:
[List: specific types of structural elements captured]

What was filtered:
[Explain: what was intentionally excluded for clarity (e.g., built-in calls, trivial imports)]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2. STRUCTURAL UNDERSTANDING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Organization:
[Describe: how code is organized - class-based, functional, mixed]

Entry points:
[Identify: where execution likely begins - main(), specific entry functions]

Responsibility distribution:
[Explain: how responsibilities are divided across classes/functions]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. INTERACTION REASONING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

How components interact:
[Describe: specific function/method call patterns observed]

Coordination patterns:
[Identify: which components orchestrate others vs which are workers]

Isolated vs connected:
[Analyze: which parts work independently vs which are tightly coupled]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4. DEPENDENCY REASONING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Component dependencies:
[Map: what depends on what, using specific names]

Structural reasons:
[Explain: why these dependencies exist based on observed structure]

Change impact:
[Analyze: if X changed, what would be affected structurally]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5. ARCHITECTURAL INSIGHT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Design pattern (if provable):
[Identify: only if clearly visible from structure - e.g., "class with methods suggests OOP", "functions calling functions suggests procedural"]

System topology:
[Classify: centralized (one main coordinator) vs modular (independent components) vs layered]

Structural strengths:
[Note: what the structure does well - separation of concerns, modularity, etc.]

Structural risks:
[Identify: potential issues visible from structure - tight coupling, single points of failure]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITICAL RULES:
- Use simple English, no jargon
- Reference specific names from the data
- Follow Observation → Interpretation → Implication
- No speculation about runtime behavior
- Keep paragraphs to 2-3 lines maximum
- Use bullet points where appropriate
- Be specific, not generic
"""

        response = model.generate_content(prompt)
        
        if response and response.text:
            reasoning = _parse_structured_reasoning(response.text)
            # Add graph-specific reasoning
            reasoning['graph_reasoning'] = _generate_graph_specific_reasoning(analysis_data)
            return reasoning
        else:
            return _generate_structured_fallback(analysis_data, filename)
            
    except Exception as e:
        print(f"Deep reasoning error: {e}")
        return _generate_structured_fallback(analysis_data, filename)


def _prepare_detailed_analysis(data: Dict[str, Any], filename: str) -> str:
    """
    Prepare comprehensive analysis data with specific names and counts.
    """
    lines = [f"FILE: {filename}", ""]
    
    # Imports
    imports = data.get('imports', [])
    if imports:
        lines.append(f"IMPORTS ({len(imports)} total):")
        stdlib = []
        external = []
        STDLIB = {'os', 'sys', 'json', 'ast', 're', 'typing', 'collections', 'itertools'}
        
        for imp in imports:
            name = imp.get('name', '') or imp.get('module', '')
            if name:
                if name.split('.')[0] in STDLIB:
                    stdlib.append(name)
                else:
                    external.append(name)
        
        if stdlib:
            lines.append(f"  Standard library: {', '.join(stdlib[:6])}")
        if external:
            lines.append(f"  External packages: {', '.join(external[:6])}")
        lines.append("")
    
    # Classes
    classes = data.get('classes', [])
    if classes:
        lines.append(f"CLASSES ({len(classes)} defined):")
        for cls in classes:
            methods = cls.get('methods', [])
            method_names = [m['name'] for m in methods[:8]]
            lines.append(f"  • {cls['name']}: {len(methods)} methods")
            lines.append(f"    Methods: {', '.join(method_names)}")
        lines.append("")
    
    # Functions
    functions = data.get('functions', [])
    if functions:
        lines.append(f"FUNCTIONS ({len(functions)} standalone):")
        func_details = []
        for func in functions:
            args = func.get('args', [])
            func_details.append(f"{func['name']}({', '.join(args[:3])})")
        lines.append(f"  {', '.join(func_details[:8])}")
        lines.append("")
    
    # Calls (interaction data)
    calls = data.get('calls', [])
    if calls:
        lines.append(f"FUNCTION CALLS ({len(calls)} observed):")
        call_map = {}
        for call in calls:
            caller = call.get('caller_scope', 'unknown')
            callee = call.get('callee', 'unknown')
            if caller != callee:
                if caller not in call_map:
                    call_map[caller] = []
                call_map[caller].append(callee)
        
        # Show top 5 callers
        for caller in list(call_map.keys())[:5]:
            callees = call_map[caller][:4]
            lines.append(f"  {caller} → {', '.join(callees)}")
        lines.append("")
    
    return "\n".join(lines)


def _parse_structured_reasoning(text: str) -> Dict[str, Any]:
    """
    Parse the structured AI response into organized sections.
    """
    result = {
        'analysis_scope': {'analyzed': '', 'extracted': '', 'filtered': ''},
        'structural_understanding': {'organization': '', 'entry_points': '', 'responsibility': ''},
        'interaction_reasoning': {'interactions': '', 'coordination': '', 'isolation': ''},
        'dependency_reasoning': {'dependencies': '', 'reasons': '', 'impact': ''},
        'architectural_insight': {'pattern': '', 'topology': '', 'strengths': '', 'risks': ''},
    }
    
    # Split into sections by the divider lines
    sections = text.split('━')
    
    current_section = None
    current_subsection = None
    current_content = []
    
    for line in text.split('\n'):
        line_strip = line.strip()
        
        # Detect main sections
        if '1. ANALYSIS SCOPE' in line_strip:
            current_section = 'analysis_scope'
            continue
        elif '2. STRUCTURAL UNDERSTANDING' in line_strip:
            current_section = 'structural_understanding'
            continue
        elif '3. INTERACTION REASONING' in line_strip:
            current_section = 'interaction_reasoning'
            continue
        elif '4. DEPENDENCY REASONING' in line_strip:
            current_section = 'dependency_reasoning'
            continue
        elif '5. ARCHITECTURAL INSIGHT' in line_strip:
            current_section = 'architectural_insight'
            continue
        
        # Skip divider lines
        if not line_strip or line_strip.startswith('━') or 'CRITICAL RULES' in line_strip:
            continue
        
        # Detect subsections (keywords followed by colon)
        if current_section:
            if current_section == 'analysis_scope':
                if line_strip.startswith('What was analyzed:'):
                    current_subsection = 'analyzed'
                    current_content = []
                elif line_strip.startswith('What was extracted:'):
                    if current_subsection:
                        result[current_section][current_subsection] = '\n'.join(current_content).strip()
                    current_subsection = 'extracted'
                    current_content = []
                elif line_strip.startswith('What was filtered:'):
                    if current_subsection:
                        result[current_section][current_subsection] = '\n'.join(current_content).strip()
                    current_subsection = 'filtered'
                    current_content = []
                elif current_subsection and line_strip:
                    # Remove the label if it's on the same line
                    content_line = line_strip
                    for prefix in ['What was analyzed:', 'What was extracted:', 'What was filtered:']:
                        if content_line.startswith(prefix):
                            content_line = content_line[len(prefix):].strip()
                    if content_line:
                        current_content.append(content_line)
            
            elif current_section == 'structural_understanding':
                if line_strip.startswith('Organization:'):
                    current_subsection = 'organization'
                    current_content = []
                elif line_strip.startswith('Entry points:'):
                    if current_subsection:
                        result[current_section][current_subsection] = '\n'.join(current_content).strip()
                    current_subsection = 'entry_points'
                    current_content = []
                elif line_strip.startswith('Responsibility distribution:'):
                    if current_subsection:
                        result[current_section][current_subsection] = '\n'.join(current_content).strip()
                    current_subsection = 'responsibility'
                    current_content = []
                elif current_subsection and line_strip:
                    content_line = line_strip
                    for prefix in ['Organization:', 'Entry points:', 'Responsibility distribution:']:
                        if content_line.startswith(prefix):
                            content_line = content_line[len(prefix):].strip()
                    if content_line:
                        current_content.append(content_line)
            
            elif current_section == 'interaction_reasoning':
                if line_strip.startswith('How components interact:'):
                    current_subsection = 'interactions'
                    current_content = []
                elif line_strip.startswith('Coordination patterns:'):
                    if current_subsection:
                        result[current_section][current_subsection] = '\n'.join(current_content).strip()
                    current_subsection = 'coordination'
                    current_content = []
                elif line_strip.startswith('Isolated vs connected:'):
                    if current_subsection:
                        result[current_section][current_subsection] = '\n'.join(current_content).strip()
                    current_subsection = 'isolation'
                    current_content = []
                elif current_subsection and line_strip:
                    content_line = line_strip
                    for prefix in ['How components interact:', 'Coordination patterns:', 'Isolated vs connected:']:
                        if content_line.startswith(prefix):
                            content_line = content_line[len(prefix):].strip()
                    if content_line:
                        current_content.append(content_line)
            
            elif current_section == 'dependency_reasoning':
                if line_strip.startswith('Component dependencies:'):
                    current_subsection = 'dependencies'
                    current_content = []
                elif line_strip.startswith('Structural reasons:'):
                    if current_subsection:
                        result[current_section][current_subsection] = '\n'.join(current_content).strip()
                    current_subsection = 'reasons'
                    current_content = []
                elif line_strip.startswith('Change impact:'):
                    if current_subsection:
                        result[current_section][current_subsection] = '\n'.join(current_content).strip()
                    current_subsection = 'impact'
                    current_content = []
                elif current_subsection and line_strip:
                    content_line = line_strip
                    for prefix in ['Component dependencies:', 'Structural reasons:', 'Change impact:']:
                        if content_line.startswith(prefix):
                            content_line = content_line[len(prefix):].strip()
                    if content_line:
                        current_content.append(content_line)
            
            elif current_section == 'architectural_insight':
                if line_strip.startswith('Design pattern'):
                    current_subsection = 'pattern'
                    current_content = []
                elif line_strip.startswith('System topology:'):
                    if current_subsection:
                        result[current_section][current_subsection] = '\n'.join(current_content).strip()
                    current_subsection = 'topology'
                    current_content = []
                elif line_strip.startswith('Structural strengths:'):
                    if current_subsection:
                        result[current_section][current_subsection] = '\n'.join(current_content).strip()
                    current_subsection = 'strengths'
                    current_content = []
                elif line_strip.startswith('Structural risks:'):
                    if current_subsection:
                        result[current_section][current_subsection] = '\n'.join(current_content).strip()
                    current_subsection = 'risks'
                    current_content = []
                elif current_subsection and line_strip:
                    content_line = line_strip
                    for prefix in ['Design pattern', 'System topology:', 'Structural strengths:', 'Structural risks:']:
                        if content_line.startswith(prefix):
                            content_line = content_line[len(prefix):].strip()
                    if content_line:
                        current_content.append(content_line)
    
    # Save last collected content
    if current_section and current_subsection and current_content:
        result[current_section][current_subsection] = '\n'.join(current_content).strip()
    
    return result


def _generate_graph_specific_reasoning(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate reasoning specific to each graph type.
    """
    calls = data.get('calls', [])
    classes = data.get('classes', [])
    imports = data.get('imports', [])
    
    return {
        'call_graph': _reason_about_call_graph(calls),
        'class_diagram': _reason_about_classes(classes),
        'import_graph': _reason_about_imports(imports),
        'visual_value': _explain_visual_value(calls, classes, imports)
    }


def _reason_about_call_graph(calls: List[Dict]) -> Dict[str, str]:
    """Call graph specific reasoning (4 subsections)."""
    if not calls:
        return {
            'entry_points': 'No function calls detected in this file.',
            'flow': 'Unable to trace execution flow without call data.',
            'control': 'No control flow visible.',
            'impact': 'No interaction topology to analyze.'
        }
    
    # Analyze entry points
    callers = set(c.get('caller_scope', '') for c in calls)
    callees = set(c.get('callee', '') for c in calls)
    entry_points = [c for c in callers if c not in callees and c not in ('global', '<module>')]
    
    entry_explanation = f"Entry points likely include: {', '.join(entry_points[:3])}. These initiate execution chains." if entry_points else "Execution appears to start from module-level or a 'main' function."
    
    # Flow analysis
    call_depth = {}
    for call in calls:
        caller = call.get('caller_scope', '')
        call_depth[caller] = call_depth.get(caller, 0) + 1
    
    main_callers = sorted(call_depth.items(), key=lambda x: x[1], reverse=True)[:3]
    flow = f"Main execution paths flow through: {', '.join([f'{c[0]} ({c[1]} calls)' for c in main_callers])}."
    
    # Control insight
    if main_callers:
        orchestrators = [c[0] for c in main_callers]
        control = f"Control is orchestrated by: {', '.join(orchestrators)}. These functions coordinate others."
    else:
        control = "System appears to have flat control structure with no dominant orchestrators."
    
    # Impact analysis
    most_called = {}
    for call in calls:
        callee = call.get('callee', '')
        most_called[callee] = most_called.get(callee, 0) + 1
    
    critical_nodes = sorted(most_called.items(), key=lambda x: x[1], reverse=True)[:3]
    if critical_nodes:
        impact = f"Critical nodes (most depended on): {', '.join([f'{n[0]} (called {n[1]}x)' for n in critical_nodes])}. Changes here have high impact."
    else:
        impact = "No particularly critical nodes identified."
    
    return {
        'entry_points': entry_explanation,
        'flow': flow,
        'control': control,
        'impact': impact
    }


def _reason_about_classes(classes: List[Dict]) -> Dict[str, str]:
    """Class diagram specific reasoning (3 subsections)."""
    if not classes:
        return {
            'responsibilities': 'No classes defined - code follows functional paradigm.',
            'methods': 'No class methods to analyze.',
            'relationships': 'No class relationships visible.'
        }
    
    # Responsibility mapping
    class_purposes = []
    for cls in classes:
        method_count = len(cls.get('methods', []))
        class_purposes.append(f"{cls['name']} ({method_count} methods)")
    
    responsibilities = f"{len(classes)} class(es) defined: {', '.join(class_purposes)}. Each encapsulates related functionality."
    
    # Method role analysis
    all_methods = []
    for cls in classes:
        for method in cls.get('methods', []):
            all_methods.append(method['name'])
    
    initializers = [m for m in all_methods if m == '__init__']
    public_methods = [m for m in all_methods if not m.startswith('_')]
    private_methods = [m for m in all_methods if m.startswith('_') and m != '__init__']
    
    methods = f"Methods: {len(initializers)} initializers, {len(public_methods)} public interfaces, {len(private_methods)} internal helpers. Shows clear interface design."
    
    # Relationship interpretation
    bases_found = any(cls.get('bases', []) for cls in classes)
    if bases_found:
        relationships = "Inheritance detected - classes extend base functionality. Suggests hierarchical design."
    else:
        relationships = "No inheritance visible - classes appear independent. Suggests composition over inheritance pattern."
    
    return {
        'responsibilities': responsibilities,
        'methods': methods,
        'relationships': relationships
    }


def _reason_about_imports(imports: List[Dict]) -> Dict[str, str]:
    """Import graph specific reasoning."""
    if not imports:
        return {
            'dependencies': 'No external dependencies - purely self-contained code.',
            'critical': 'No import dependencies to analyze.'
        }
    
    STDLIB = {'os', 'sys', 'json', 'ast', 're', 'typing', 'collections', 'itertools', 'functools', 'pathlib', 'datetime'}
    
    stdlib_imports = []
    external_imports = []
    
    for imp in imports:
        name = imp.get('name', '') or imp.get('module', '')
        if name:
            if name.split('.')[0] in STDLIB:
                stdlib_imports.append(name)
            else:
                external_imports.append(name)
    
    dep_summary = f"Imports: {len(stdlib_imports)} standard library, {len(external_imports)} external packages."
    
    if external_imports:
        critical = f"Critical external dependencies: {', '.join(external_imports[:4])}. Code requires these to function."
    else:
        critical = "No external dependencies - relies only on Python standard library. Highly portable."
    
    return {
        'dependencies': dep_summary,
        'critical': critical
    }


def _explain_visual_value(calls: List, classes: List, imports: List) -> str:
    """
    Explain why graphs matter - what they reveal that text cannot.
    """
    insights = []
    
    if calls:
        insights.append("Call graph reveals execution topology that's invisible in linear code - you see the network of interactions at a glance.")
    
    if classes:
        insights.append("Class diagram exposes responsibility boundaries and interface design patterns not obvious from reading code sequentially.")
    
    if imports:
        insights.append("Import graph shows external dependencies and potential coupling risks immediately visible.")
    
    if not insights:
        insights.append("Visualizations transform linear code into spatial understanding.")
    
    return " ".join(insights)


def _generate_structured_fallback(data: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """
    Generate structured fallback reasoning when AI unavailable.
    Based purely on AST analysis.
    """
    imports = data.get('imports', [])
    classes = data.get('classes', [])
    functions = data.get('functions', [])
    calls = data.get('calls', [])
    
    # Layer 1: Analysis Scope
    analyzed = f"Analyzed {filename}: extracted {len(classes)} classes, {len(functions)} functions, {len(imports)} imports, {len(calls)} function calls."
    extracted = f"Extracted: class definitions with methods, standalone functions with signatures, import statements, and function call relationships."
    filtered = f"Filtered out: built-in function calls (print, len, etc.) and standard operators for visual clarity."
    
    # Layer 2: Structural Understanding
    if classes and functions:
        organization = f"Mixed paradigm: {len(classes)} class(es) for object-oriented structure, {len(functions)} standalone function(s) for procedural logic."
    elif classes:
        organization = f"Object-oriented design with {len(classes)} class(es) encapsulating behavior and state."
    elif functions:
        organization = f"Functional design with {len(functions)} standalone function(s)."
    else:
        organization = "Minimal structure - primarily module-level code."
    
    entry_points = "Entry point likely at module level or 'main()' function if defined."
    responsibility = f"Responsibilities distributed across {len(classes) + len(functions)} defined components."
    
    # Layer 3: Interaction Reasoning
    if calls:
        interactions = f"{len(calls)} function calls observed, showing active inter-component communication."
        coordination = "Some components orchestrate others through function calls."
        isolation = "Components with no incoming/outgoing calls are isolated; others are interconnected."
    else:
        interactions = "No function calls detected - components appear independent or code is declarative."
        coordination = "No visible coordination patterns."
        isolation = "All components appear isolated from each other."
    
    # Layer 4: Dependency Reasoning
    if calls or imports:
        dependencies = f"Dependencies exist through {len(calls)} internal calls and {len(imports)} external imports."
        reasons = "Dependencies arise from functional decomposition and external library usage."
        impact = "Changes to heavily-called functions or imported modules would ripple through the system."
    else:
        dependencies = "Minimal dependencies detected."
        reasons = "Code appears self-contained."
        impact = "Low change impact due to minimal coupling."
    
    # Layer 5: Architectural Insight
    if classes:
        pattern = "Object-oriented pattern evident from class-based structure."
        topology = "Modular topology with encapsulated responsibilities in classes."
    elif functions:
        pattern = "Procedural pattern with function-based decomposition."
        topology = "Functional topology with discrete processing units."
    else:
        pattern = "Script-like structure with linear execution."
        topology = "Simple, centralized topology."
    
    strengths = "Clear separation of concerns" if (classes or functions) else "Simplicity"
    risks = "Tight coupling through direct calls" if calls else "Limited reusability"
    
    return {
        'analysis_scope': {
            'analyzed': analyzed,
            'extracted': extracted,
            'filtered': filtered
        },
        'structural_understanding': {
            'organization': organization,
            'entry_points': entry_points,
            'responsibility': responsibility
        },
        'interaction_reasoning': {
            'interactions': interactions,
            'coordination': coordination,
            'isolation': isolation
        },
        'dependency_reasoning': {
            'dependencies': dependencies,
            'reasons': reasons,
            'impact': impact
        },
        'architectural_insight': {
            'pattern': pattern,
            'topology': topology,
            'strengths': strengths,
            'risks': risks
        },
        'graph_reasoning': _generate_graph_specific_reasoning(data)
    }


def get_data_flow_reasoning(analysis_data: Dict[str, Any], filename: str, data_flow_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate reasoning about how data flows through the system.
    
    Args:
        analysis_data: AST analysis results
        filename: Name of the analyzed file
        data_flow_analysis: Results from data_flow_analyzer
    
    Returns:
        Dict with entry, processing, coordination, exit explanations + diagram explanation
    """
    entry_points = data_flow_analysis.get('entry_points', [])
    processing_stages = data_flow_analysis.get('processing_stages', [])
    coordinators = data_flow_analysis.get('coordinators', [])
    exit_points = data_flow_analysis.get('exit_points', [])
    
    # Entry points explanation
    if entry_points:
        entry_names = [ep['name'] for ep in entry_points[:5]]
        entry_explanation = f"Data enters through {len(entry_points)} function(s)/method(s): {', '.join(entry_names)}. These accept input parameters."
    else:
        entry_explanation = "No clear data entry points detected - code may use global state or constants."
    
    # Processing stages explanation
    if processing_stages:
        proc_names = [ps['name'] for ps in processing_stages[:5]]
        processing_explanation = f"Data is processed by {len(processing_stages)} component(s): {', '.join(proc_names)}. These transform or analyze input data."
    else:
        processing_explanation = "No explicit data processing stages identified - code may perform minimal transformations."
    
    # Coordination explanation
    if coordinators:
        coord_names = [c['name'] for c in coordinators[:4]]
        coordination_explanation = f"Data flow is coordinated by {len(coordinators)} orchestrator(s): {', '.join(coord_names)}. These route data between components."
    else:
        coordination_explanation = "No coordination layer detected - data flows directly between entry and processing."
    
    # Exit points explanation
    if exit_points:
        exit_names = [ex['name'] for ex in exit_points[:5]]
        exit_explanation = f"Data exits through {len(exit_points)} function(s): {', '.join(exit_names)}. These return, save, or output results."
    else:
        exit_explanation = "No explicit exit points identified - results may be stored in global state or returned implicitly."
    
    # Diagram explanation
    total_nodes = len(entry_points) + len(processing_stages) + len(coordinators) + len(exit_points)
    if total_nodes > 0:
        diagram_explanation = (
            f"The diagram shows a top-to-bottom flow of data through {total_nodes} component(s). "
            f"Parallelogram shapes mark data inputs, rectangles show processing steps, "
            f"rounded rectangles indicate coordinators, and ovals represent outputs. "
            f"This structure matters because it reveals the complete data transformation pipeline at a glance."
        )
    else:
        diagram_explanation = "No clear data flow structure detected in this file."
    
    # Connection to other graphs
    connection = (
        "While the Call Graph shows 'who calls whom', and the Class Diagram shows 'who owns what', "
        "this Data Flow diagram specifically shows 'what moves where' - tracking how information "
        "enters, transforms, and exits the system. This completes the architectural understanding."
    )
    
    return {
        'entry_explanation': entry_explanation,
        'processing_explanation': processing_explanation,
        'coordination_explanation': coordination_explanation,
        'exit_explanation': exit_explanation,
        'diagram_explanation': diagram_explanation,
        'connection_to_graphs': connection
    }

