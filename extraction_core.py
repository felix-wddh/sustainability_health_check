"""
extraction_core.py - Pure functions for Excel data extraction with provenance tracking.

This module provides API-ready extraction logic that can be used by both
Streamlit UI and future API endpoints. No Streamlit dependencies.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Tuple

import pandas as pd


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class Provenance:
    """Tracks where a value was extracted from."""
    method: Literal["anchor", "table", "manual", "failed"]
    sheet: str
    cell_ref: str  # e.g., "C15" or "SUM(B2:B100)"
    anchor_text: Optional[str] = None  # The label text that was matched
    confidence: float = 1.0  # 0.0-1.0
    
    def to_dict(self) -> dict:
        return {
            "method": self.method,
            "sheet": self.sheet,
            "cell_ref": self.cell_ref,
            "anchor_text": self.anchor_text,
            "confidence": self.confidence,
        }


@dataclass
class ExtractionResult:
    """Result of extracting all required inputs from a workbook."""
    inputs: Dict[str, float]
    provenance: Dict[str, Provenance]
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "inputs": self.inputs,
            "provenance": {k: v.to_dict() for k, v in self.provenance.items()},
            "warnings": self.warnings,
        }


# ============================================================================
# Constants
# ============================================================================

REQUIRED_KEYS = [
    "Transport_kgCO2e",
    "Materials_kgCO2e",
    "Production_kgCO2e",
    "Use_kWh_per_year",
]

# Anchor synonyms for label-based extraction (case-insensitive)
# NOTE: CO2 keys require explicit CO2/emission context to avoid false positives
ANCHOR_SYNONYMS: Dict[str, List[str]] = {
    "Use_kWh_per_year": [
        "annual energy consumption",
        "energy consumption",
        "consumo de energía",
        "consumo anual",
        "kwh/year",
        "kwh per year",
        "kwh/a",
        "kwh/año",
        "electricity consumption",
        "power consumption",
        "annual consumption",
        "yearly consumption",
        "use phase energy",
        "energy use",
    ],
    # These require CO2/emission context to avoid matching generic labels
    "Transport_kgCO2e": [
        "transport co2",
        "transport kgco2",
        "transport emissions",
        "logistics co2",
        "logistics emissions",
        "shipping co2",
        "co2 transport",
        "co2e transport",
        "transporte co2",
        "a1-a2",  # LCA phase codes
    ],
    "Materials_kgCO2e": [
        "materials co2",
        "materials kgco2",
        "material emissions",
        "materials emissions",
        "raw materials co2",
        "bom co2",
        "co2 materials",
        "co2e materials",
        "materiales co2",
        "a1-a3",  # LCA phase codes
        "upstream emissions",
    ],
    "Production_kgCO2e": [
        "production co2",
        "production kgco2",
        "production emissions",
        "manufacturing co2",
        "manufacturing emissions",
        "assembly co2",
        "factory co2",
        "co2 production",
        "co2e production",
        "producción co2",
        "a3",  # LCA phase codes
    ],
}

# Header synonyms for table-based extraction
HEADER_SYNONYMS: Dict[str, List[str]] = {
    "Transport_kgCO2e": ["transport", "logistics", "shipping", "co2e_transport", "co2_transport"],
    "Materials_kgCO2e": ["material", "materials", "bill of materials", "bom", "co2e_material", "co2_material"],
    "Production_kgCO2e": ["production", "manufacturing", "factory", "co2e_production", "co2_production"],
    "Use_kWh_per_year": ["kwh/a", "kwh per year", "annual consumption", "use_kwh", "energy_use", "kwh/year"],
}


# ============================================================================
# Parsing Helpers
# ============================================================================

def normalize(s: str) -> str:
    """Normalize string for comparison."""
    return re.sub(r"\s+", " ", str(s).strip().lower())


def parse_numeric_with_unit(value) -> Tuple[Optional[float], str]:
    """
    Parse a value that may contain units like "409.6 kWh" or "322 kWh/year".
    
    Returns:
        Tuple of (parsed_float or None, original_string)
    """
    if value is None:
        return None, ""
    
    if isinstance(value, (int, float)):
        return float(value), str(value)
    
    s = str(value).strip()
    if not s or s.lower() in ("nan", "none", ""):
        return None, s
    
    # Remove common unit suffixes
    cleaned = re.sub(r"\s*(kwh|kgco2e?|kg\s*co2|%|per\s*year|/year|/a|/año)\s*$", "", s, flags=re.IGNORECASE)
    
    # Handle comma as decimal separator (European format)
    # Rule: "1,200" (3 digits after comma) = thousand separator = 1200
    #       "1,2" or "1,20" (1-2 digits after comma) = decimal separator = 1.2 or 1.20
    if "," in cleaned and "." not in cleaned:
        parts = cleaned.split(",")
        if len(parts) == 2 and parts[1].isdigit():
            if len(parts[1]) >= 3:
                # 3+ digits after comma = thousand separator
                cleaned = cleaned.replace(",", "")
            else:
                # 1-2 digits after comma = decimal separator (European format)
                cleaned = cleaned.replace(",", ".")
        else:
            # Multiple commas or non-digit - remove all commas
            cleaned = cleaned.replace(",", "")
    
    # Remove any remaining non-numeric characters except . and -
    cleaned = re.sub(r"[^\d.\-]", "", cleaned)
    
    try:
        return float(cleaned), s
    except (ValueError, TypeError):
        return None, s


def col_index_to_letter(col_idx: int) -> str:
    """Convert 0-based column index to Excel column letter (A, B, ..., Z, AA, AB, ...)."""
    result = ""
    while col_idx >= 0:
        result = chr(col_idx % 26 + ord('A')) + result
        col_idx = col_idx // 26 - 1
    return result


# ============================================================================
# Anchor-Based Extraction
# ============================================================================

def find_anchor_value(
    df: pd.DataFrame,
    anchors: List[str],
    sheet_name: str,
) -> Tuple[Optional[float], Optional[Provenance]]:
    """
    Search for anchor text and extract the nearest numeric value.
    
    Strategy:
    1. Find cells containing anchor text
    2. Look for numeric value in same row (prefer rightward cells)
    3. If not found, look in cell directly below
    
    Returns:
        Tuple of (value, provenance) or (None, None) if not found
    """
    df_str = df.astype(str).fillna("")
    
    for anchor in anchors:
        anchor_norm = normalize(anchor)
        
        # Search all cells for anchor match
        for row_idx in range(len(df)):
            for col_idx in range(df.shape[1]):
                cell_val = normalize(df_str.iloc[row_idx, col_idx])
                
                if anchor_norm in cell_val:
                    # Found anchor! Now look for numeric value
                    
                    # Strategy 1: Look rightward in same row
                    for search_col in range(col_idx + 1, df.shape[1]):
                        val, orig = parse_numeric_with_unit(df.iloc[row_idx, search_col])
                        if val is not None and val > 0:
                            cell_ref = f"{col_index_to_letter(search_col)}{row_idx + 1}"
                            return val, Provenance(
                                method="anchor",
                                sheet=sheet_name,
                                cell_ref=cell_ref,
                                anchor_text=df_str.iloc[row_idx, col_idx][:50],
                                confidence=0.9,
                            )
                    
                    # Strategy 2: Look in same column, next row
                    if row_idx + 1 < len(df):
                        val, orig = parse_numeric_with_unit(df.iloc[row_idx + 1, col_idx])
                        if val is not None and val > 0:
                            cell_ref = f"{col_index_to_letter(col_idx)}{row_idx + 2}"
                            return val, Provenance(
                                method="anchor",
                                sheet=sheet_name,
                                cell_ref=cell_ref,
                                anchor_text=df_str.iloc[row_idx, col_idx][:50],
                                confidence=0.8,
                            )
                    
                    # Strategy 3: Look leftward (value before label)
                    for search_col in range(col_idx - 1, -1, -1):
                        val, orig = parse_numeric_with_unit(df.iloc[row_idx, search_col])
                        if val is not None and val > 0:
                            cell_ref = f"{col_index_to_letter(search_col)}{row_idx + 1}"
                            return val, Provenance(
                                method="anchor",
                                sheet=sheet_name,
                                cell_ref=cell_ref,
                                anchor_text=df_str.iloc[row_idx, col_idx][:50],
                                confidence=0.7,
                            )
    
    return None, None


# ============================================================================
# Table-Based Extraction
# ============================================================================

def detect_header_row(df: pd.DataFrame, max_check: int = 15) -> int:
    """Detect the most likely header row using keyword hits."""
    keys = [k for v in HEADER_SYNONYMS.values() for k in v]
    best_row, best_hits = 0, -1
    
    for i in range(min(max_check, len(df))):
        hits = 0
        row_vals = df.iloc[i].astype(str).fillna("").tolist()
        row_norm = [normalize(x) for x in row_vals]
        for cell in row_norm:
            for k in keys:
                if k in cell:
                    hits += 1
        if hits > best_hits:
            best_hits, best_row = hits, i
    
    return best_row


def map_headers(headers: List[str]) -> Dict[str, Optional[int]]:
    """Map header names to column indices using synonyms."""
    mapped: Dict[str, Optional[int]] = {k: None for k in REQUIRED_KEYS}
    nheaders = [normalize(h) for h in headers]
    
    for key, syns in HEADER_SYNONYMS.items():
        for i, h in enumerate(nheaders):
            if not headers[i]:
                continue
            if any(s in h for s in syns):
                mapped[key] = i
                break
    
    return mapped


def extract_table_value(
    df: pd.DataFrame,
    col_idx: Optional[int],
    sheet_name: str,
    key: str,
) -> Tuple[Optional[float], Optional[Provenance]]:
    """Extract value from a column (table-based approach).
    
    For Use_kWh_per_year and similar per-unit values, we take the first valid value.
    This is because each row represents a different product/variant.
    """
    if col_idx is None or col_idx < 0 or col_idx >= df.shape[1]:
        return None, None
    
    # Find first non-null numeric value in the column
    col_letter = col_index_to_letter(col_idx)
    
    for row_idx in range(len(df)):
        cell_val = df.iloc[row_idx, col_idx]
        parsed, _ = parse_numeric_with_unit(cell_val)
        if parsed is not None and parsed > 0:
            cell_ref = f"{col_letter}{row_idx + 2}"  # +2 because header row + 1-indexed
            return parsed, Provenance(
                method="table",
                sheet=sheet_name,
                cell_ref=cell_ref,
                anchor_text=None,
                confidence=0.6,
            )
    
    return None, None


# ============================================================================
# Main Extraction Function
# ============================================================================

def extract_required_inputs(
    workbook_bytes: bytes,
    model_sheet: str,
) -> ExtractionResult:
    """
    Extract all required inputs from a workbook using the specified model sheet.
    
    Extraction priority:
    1. Anchor-based (label/value pairs)
    2. Table-based (header row + column sum)
    
    Args:
        workbook_bytes: Excel file content as bytes
        model_sheet: Name of the sheet to extract from
        
    Returns:
        ExtractionResult with inputs, provenance, and warnings
    """
    inputs: Dict[str, float] = {}
    provenance: Dict[str, Provenance] = {}
    warnings: List[str] = []
    
    try:
        xls = pd.ExcelFile(io.BytesIO(workbook_bytes))
    except Exception as e:
        warnings.append(f"Failed to read workbook: {e}")
        return ExtractionResult(inputs={k: 0.0 for k in REQUIRED_KEYS}, provenance={}, warnings=warnings)
    
    if model_sheet not in xls.sheet_names:
        warnings.append(f"Sheet '{model_sheet}' not found. Available: {xls.sheet_names}")
        return ExtractionResult(inputs={k: 0.0 for k in REQUIRED_KEYS}, provenance={}, warnings=warnings)
    
    # Read the target sheet
    df = xls.parse(model_sheet, header=None, dtype=str)
    
    for key in REQUIRED_KEYS:
        value: Optional[float] = None
        prov: Optional[Provenance] = None
        
        # Priority 1: Anchor-based extraction
        anchors = ANCHOR_SYNONYMS.get(key, [])
        if anchors:
            value, prov = find_anchor_value(df, anchors, model_sheet)
        
        # Priority 2: Table-based extraction (fallback)
        if value is None:
            header_row = detect_header_row(df)
            headers = [
                str(h).strip() if str(h).strip().lower() not in ("nan", "none") else ""
                for h in df.iloc[header_row].tolist()
            ]
            mapping = map_headers(headers)
            col_idx = mapping.get(key)
            
            if col_idx is not None:
                body = df.iloc[header_row + 1:].reset_index(drop=True)
                value, prov = extract_table_value(body, col_idx, model_sheet, key)
        
        # Record result
        if value is not None and prov is not None:
            inputs[key] = value
            provenance[key] = prov
        else:
            inputs[key] = 0.0
            provenance[key] = Provenance(
                method="failed",
                sheet=model_sheet,
                cell_ref="N/A",
                anchor_text=None,
                confidence=0.0,
            )
            warnings.append(f"Could not extract '{key}' from sheet '{model_sheet}'")
    
    return ExtractionResult(inputs=inputs, provenance=provenance, warnings=warnings)


def load_workbook_sheets(workbook_bytes: bytes) -> Dict[str, pd.DataFrame]:
    """Load all sheets from a workbook as DataFrames."""
    xls = pd.ExcelFile(io.BytesIO(workbook_bytes))
    return {sheet: xls.parse(sheet, header=None, dtype=str) for sheet in xls.sheet_names}


def detect_model_sheets(sheet_names: List[str]) -> List[str]:
    """
    Identify likely model/product sheets from sheet names.
    
    Looks for patterns like:
    - "Dryer SMG...", "Dryer GTD..."
    - Sheets with SKU patterns in parentheses
    - Product category prefixes (Washer, Cooler, Refrigerator, etc.)
    """
    patterns = [
        r"^(dryer|washer|cooler|refrigerator|fridge|cooling|cooking|washing)",
        r"\([A-Z0-9]{3,}\)",  # SKU in parentheses
        r"(GTD|SMG|WTW|WMH|GFE|GSS)",  # Common Mabe/GE model prefixes
    ]
    
    model_sheets = []
    for name in sheet_names:
        name_lower = name.lower()
        for pattern in patterns:
            if re.search(pattern, name_lower, re.IGNORECASE):
                model_sheets.append(name)
                break
    
    return model_sheets if model_sheets else sheet_names[:1]  # Fallback to first sheet


# ============================================================================
# KPI Computation (Pure Function)
# ============================================================================

def compute_kpis(
    inputs: Dict[str, float],
    grid_factor: float,
    lifetime: int,
) -> Dict[str, float]:
    """
    Compute CO2e KPIs from inputs.
    
    Args:
        inputs: Dict with Transport_kgCO2e, Materials_kgCO2e, Production_kgCO2e, Use_kWh_per_year
        grid_factor: kg CO2e per kWh
        lifetime: Product lifetime in years
        
    Returns:
        Dict with phase values, totals, and shares
    """
    t = float(inputs.get("Transport_kgCO2e", 0) or 0)
    m = float(inputs.get("Materials_kgCO2e", 0) or 0)
    p = float(inputs.get("Production_kgCO2e", 0) or 0)
    kwh = float(inputs.get("Use_kWh_per_year", 0) or 0)
    
    use = kwh * grid_factor * lifetime
    total = t + m + p + use
    
    if total > 0:
        share_t = t / total * 100.0
        share_m = m / total * 100.0
        share_p = p / total * 100.0
        share_use = use / total * 100.0
    else:
        share_t = share_m = share_p = share_use = 0.0
    
    return {
        "Transport_kgCO2e": round(t, 2),
        "Materials_kgCO2e": round(m, 2),
        "Production_kgCO2e": round(p, 2),
        "Use_kWh_per_year": round(kwh, 2),
        "UsePhase_CO2e": round(use, 2),
        "Total_CO2e": round(total, 2),
        "Share_Transport_%": round(share_t, 1),
        "Share_Materials_%": round(share_m, 1),
        "Share_Production_%": round(share_p, 1),
        "Share_Use_%": round(share_use, 1),
    }
