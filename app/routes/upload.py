from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import PlainTextResponse
from app.services.ast_parser import analyze_code
from app.services.graph_builder import generate_call_graph, generate_class_diagram, generate_import_graph
from app.services.mermaid_generator import generate_call_graph_mermaid, generate_class_diagram_mermaid, generate_import_graph_mermaid, generate_data_flow_diagram
from app.services.ai_reasoning import get_deep_reasoning, get_data_flow_reasoning
from app.services.data_flow_analyzer import analyze_data_flow
from app.services.report_generator import generate_text_report

router = APIRouter(prefix="/upload", tags=["upload"])
templates = Jinja2Templates(directory="app/templates")

# Store last analysis for report download
last_analysis = {}

@router.post("/")
async def upload_file(request: Request, file: UploadFile = File(...)):
    global last_analysis
    
    if not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Only .py files are supported in MVP.")
    
    try:
        content = await file.read()
        source_code = content.decode("utf-8")
        
        # Deterministic Analysis (AST-based)
        analysis_result = analyze_code(source_code)
        
        if "error" in analysis_result:
             raise HTTPException(status_code=400, detail=analysis_result["error"])

        # Store for report download
        last_analysis = {"data": analysis_result, "filename": file.filename}

        # Generate PNG graphs (matplotlib)
        call_graph_url = generate_call_graph(analysis_result.get("calls", []), file.filename)
        class_diagram_url = generate_class_diagram(analysis_result.get("classes", []), file.filename)
        import_graph_url = generate_import_graph(analysis_result.get("imports", []), file.filename)
        
        # Generate Mermaid diagrams (interactive)
        call_graph_mermaid = generate_call_graph_mermaid(analysis_result.get("calls", []))
        class_diagram_mermaid = generate_class_diagram_mermaid(analysis_result.get("classes", []))
        import_graph_mermaid = generate_import_graph_mermaid(analysis_result.get("imports", []), file.filename)
        
        # Generate deep structured reasoning (uses Gemini if available)
        deep_reasoning = get_deep_reasoning(analysis_result, file.filename)
        
        # Analyze data flow
        data_flow_analysis = analyze_data_flow(analysis_result)
        data_flow_diagram = generate_data_flow_diagram(data_flow_analysis)
        data_flow_reasoning = get_data_flow_reasoning(analysis_result, file.filename, data_flow_analysis)
        
        # Generate text report
        text_report = generate_text_report(analysis_result, file.filename)

        return templates.TemplateResponse("results.html", {
            "request": request, 
            "filename": file.filename,
            "data": analysis_result,
            # PNG graphs
            "call_graph_url": call_graph_url,
            "class_diagram_url": class_diagram_url,
            "import_graph_url": import_graph_url,
            # Mermaid diagrams
            "call_graph_mermaid": call_graph_mermaid,
            "class_diagram_mermaid": class_diagram_mermaid,
            "import_graph_mermaid": import_graph_mermaid,
            # Deep structured reasoning
            "deep_reasoning": deep_reasoning,
            # Data flow analysis
            "data_flow_analysis": data_flow_analysis,
            "data_flow_diagram": data_flow_diagram,
            "data_flow_reasoning": data_flow_reasoning,
            # Text report
            "text_report": text_report
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/report")
async def download_report():
    """Download the text report as a file."""
    global last_analysis
    
    if not last_analysis:
        raise HTTPException(status_code=404, detail="No analysis available. Upload a file first.")
    
    report = generate_text_report(last_analysis["data"], last_analysis["filename"])
    
    return PlainTextResponse(
        content=report,
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=report_{last_analysis['filename']}.txt"
        }
    )
