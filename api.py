"""
api.py - Minimal FastAPI wrapper for the extraction and KPI computation logic.

This provides a programmatic API for integration with other systems.

Usage:
    uvicorn api:app --reload --port 8000
    
    curl -X POST http://localhost:8000/compute \
        -F "file=@fixtures/dryer_workbook.xlsx" \
        -F "model_sheet=Dryer SMG (SMG6527)" \
        -F "grid_factor=0.25" \
        -F "lifetime=10"
"""

from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from extraction_core import (
    extract_required_inputs,
    compute_kpis,
    detect_model_sheets,
    load_workbook_sheets,
)


app = FastAPI(
    title="Mabe PaceSetter API",
    description="API for extracting sustainability inputs from Excel workbooks and computing CO2e KPIs.",
    version="1.0.0",
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Mabe PaceSetter API is running"}


@app.get("/sheets")
async def get_sheets(file: UploadFile = File(...)):
    """List available sheets in the workbook and detect model sheets."""
    try:
        content = await file.read()
        sheets = load_workbook_sheets(content)
        model_sheets = detect_model_sheets(list(sheets.keys()))
        
        return {
            "all_sheets": list(sheets.keys()),
            "detected_model_sheets": model_sheets,
            "recommended_sheet": model_sheets[0] if model_sheets else None,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read workbook: {str(e)}")


@app.post("/compute")
async def compute(
    file: UploadFile = File(..., description="Excel workbook file (.xlsx, .xlsm, .xls)"),
    model_sheet: str = Form(..., description="Name of the sheet to extract data from"),
    grid_factor: float = Form(0.25, description="Electricity grid factor in kg CO2e/kWh"),
    lifetime: int = Form(10, description="Product lifetime in years"),
):
    """
    Extract inputs from workbook and compute CO2e KPIs.
    
    Returns:
        - inputs: Extracted values for each required key
        - provenance: Source information for each extraction
        - warnings: Any extraction warnings
        - kpis: Computed KPI values including totals and shares
    """
    try:
        content = await file.read()
        
        # Extract inputs
        extraction = extract_required_inputs(content, model_sheet)
        
        # Compute KPIs
        kpis = compute_kpis(extraction.inputs, grid_factor, lifetime)
        
        return JSONResponse(content={
            "inputs": extraction.inputs,
            "provenance": {k: v.to_dict() for k, v in extraction.provenance.items()},
            "warnings": extraction.warnings,
            "kpis": kpis,
            "parameters": {
                "model_sheet": model_sheet,
                "grid_factor": grid_factor,
                "lifetime": lifetime,
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Computation failed: {str(e)}")


@app.post("/extract")
async def extract_only(
    file: UploadFile = File(..., description="Excel workbook file"),
    model_sheet: str = Form(..., description="Name of the sheet to extract data from"),
):
    """
    Extract inputs from workbook without computing KPIs.
    
    Useful for previewing extraction results before computation.
    """
    try:
        content = await file.read()
        extraction = extract_required_inputs(content, model_sheet)
        
        return JSONResponse(content={
            "inputs": extraction.inputs,
            "provenance": {k: v.to_dict() for k, v in extraction.provenance.items()},
            "warnings": extraction.warnings,
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
