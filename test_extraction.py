"""
test_extraction.py - Pytest tests for extraction_core module.

Tests cover:
A. Different model sheets produce different extracted inputs
B. Different workbooks produce different extracted inputs
C. Provenance is present and non-empty for extractions
D. KPI totals differ when inputs differ
"""

import os
import pytest
from extraction_core import (
    extract_required_inputs,
    compute_kpis,
    parse_numeric_with_unit,
    find_anchor_value,
    detect_model_sheets,
    Provenance,
)
import pandas as pd

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def read_fixture(filename: str) -> bytes:
    """Read a fixture file as bytes."""
    path = os.path.join(FIXTURES_DIR, filename)
    with open(path, "rb") as f:
        return f.read()


# ============================================================================
# Unit Tests for Parsing
# ============================================================================

class TestParseNumericWithUnit:
    """Tests for parse_numeric_with_unit function."""
    
    def test_plain_number(self):
        val, _ = parse_numeric_with_unit(409.6)
        assert val == 409.6
    
    def test_string_with_kwh(self):
        val, _ = parse_numeric_with_unit("409.6 kWh")
        assert val == 409.6
    
    def test_string_with_kwh_year(self):
        val, _ = parse_numeric_with_unit("322 kWh/year")
        assert val == 322.0
    
    def test_comma_decimal_european(self):
        val, _ = parse_numeric_with_unit("385,5")
        assert val == 385.5
    
    def test_thousand_separator(self):
        val, _ = parse_numeric_with_unit("1,200")
        assert val == 1200.0
    
    def test_none_value(self):
        val, _ = parse_numeric_with_unit(None)
        assert val is None
    
    def test_empty_string(self):
        val, _ = parse_numeric_with_unit("")
        assert val is None


# ============================================================================
# Integration Tests for Extraction
# ============================================================================

@pytest.fixture(scope="module")
def ensure_fixtures():
    """Ensure test fixtures exist before running tests."""
    if not os.path.exists(FIXTURES_DIR):
        # Create fixtures if they don't exist
        import create_test_fixtures
        create_test_fixtures.main()
    return True


class TestDifferentSheetsDifferentValues:
    """A: Different model sheets MUST produce different extracted inputs."""
    
    def test_smg_vs_gtd_sheets(self, ensure_fixtures):
        """SMG sheet should have ~409.6 kWh, GTD should have ~245 kWh."""
        workbook = read_fixture("dryer_workbook.xlsx")
        
        # Extract from SMG sheet
        result_smg = extract_required_inputs(workbook, "Dryer SMG (SMG6527)")
        kwh_smg = result_smg.inputs.get("Use_kWh_per_year", 0)
        
        # Extract from GTD sheet
        result_gtd = extract_required_inputs(workbook, "Dryer GTD (GTD42XXX)")
        kwh_gtd = result_gtd.inputs.get("Use_kWh_per_year", 0)
        
        # Values should be different
        assert kwh_smg != kwh_gtd, "SMG and GTD should have different kWh values"
        
        # Values should be close to expected
        assert 400 < kwh_smg < 420, f"SMG kWh should be ~409.6, got {kwh_smg}"
        assert 240 < kwh_gtd < 250, f"GTD kWh should be ~245, got {kwh_gtd}"


class TestDifferentWorkbooksDifferentValues:
    """B: Different workbooks MUST produce different extracted inputs."""
    
    def test_dryer_vs_refrigerator(self, ensure_fixtures):
        """Dryer and Refrigerator workbooks should have different values."""
        dryer_wb = read_fixture("dryer_workbook.xlsx")
        fridge_wb = read_fixture("refrigerator_workbook.xlsx")
        
        # Extract from dryer (SMG sheet)
        result_dryer = extract_required_inputs(dryer_wb, "Dryer SMG (SMG6527)")
        kwh_dryer = result_dryer.inputs.get("Use_kWh_per_year", 0)
        
        # Extract from refrigerator
        result_fridge = extract_required_inputs(fridge_wb, "Cooling Unit (GSS25XXX)")
        kwh_fridge = result_fridge.inputs.get("Use_kWh_per_year", 0)
        
        # Values should be different
        assert kwh_dryer != kwh_fridge, "Dryer and Fridge should have different kWh"
        
        # Check expected ranges
        assert 400 < kwh_dryer < 420, f"Dryer kWh should be ~409.6, got {kwh_dryer}"
        assert 315 < kwh_fridge < 330, f"Fridge kWh should be ~322, got {kwh_fridge}"


class TestKPIDiffers:
    """A.2/B.2: KPI totals differ when inputs differ."""
    
    def test_kpi_differs_between_sheets(self, ensure_fixtures):
        """KPI total should differ between SMG and GTD models."""
        workbook = read_fixture("dryer_workbook.xlsx")
        
        result_smg = extract_required_inputs(workbook, "Dryer SMG (SMG6527)")
        result_gtd = extract_required_inputs(workbook, "Dryer GTD (GTD42XXX)")
        
        # Compute KPIs with same grid factor and lifetime
        grid_factor = 0.25
        lifetime = 10
        
        kpi_smg = compute_kpis(result_smg.inputs, grid_factor, lifetime)
        kpi_gtd = compute_kpis(result_gtd.inputs, grid_factor, lifetime)
        
        # Totals should differ
        assert kpi_smg["Total_CO2e"] != kpi_gtd["Total_CO2e"], \
            "KPI totals should differ between models"
        
        # SMG has higher energy, so should have higher total
        assert kpi_smg["Total_CO2e"] > kpi_gtd["Total_CO2e"], \
            "SMG (409.6 kWh) should have higher CO2e than GTD (245 kWh)"


class TestProvenancePresent:
    """C: Provenance is present and non-empty for extractions."""
    
    def test_provenance_for_successful_extraction(self, ensure_fixtures):
        """Successful extraction should have valid provenance."""
        workbook = read_fixture("dryer_workbook.xlsx")
        result = extract_required_inputs(workbook, "Dryer SMG (SMG6527)")
        
        # Check provenance for Use_kWh_per_year
        prov = result.provenance.get("Use_kWh_per_year")
        assert prov is not None, "Provenance should exist for Use_kWh_per_year"
        assert prov.method in ("anchor", "table"), f"Method should be anchor or table, got {prov.method}"
        assert prov.sheet == "Dryer SMG (SMG6527)", f"Sheet should match, got {prov.sheet}"
        assert prov.cell_ref != "N/A", f"Cell ref should be valid, got {prov.cell_ref}"
        assert prov.confidence > 0, f"Confidence should be > 0, got {prov.confidence}"
    
    def test_provenance_for_all_keys(self, ensure_fixtures):
        """All extracted keys should have provenance."""
        workbook = read_fixture("dryer_workbook.xlsx")
        result = extract_required_inputs(workbook, "Dryer SMG (SMG6527)")
        
        for key in ["Transport_kgCO2e", "Materials_kgCO2e", "Production_kgCO2e", "Use_kWh_per_year"]:
            prov = result.provenance.get(key)
            assert prov is not None, f"Provenance should exist for {key}"
            print(f"{key}: {result.inputs.get(key)} from {prov.cell_ref} ({prov.method})")


class TestTableFormatExtraction:
    """Test extraction from table-format workbooks."""
    
    def test_table_format_extraction(self, ensure_fixtures):
        """Should extract values from header-row table format."""
        workbook = read_fixture("washer_table_format.xlsx")
        result = extract_required_inputs(workbook, "Products Table")
        
        # Table format takes first valid row value
        kwh = result.inputs.get("Use_kWh_per_year", 0)
        
        # First row has 175.5 kWh
        assert 170 < kwh < 180, f"Table extraction should get first row ~175.5, got {kwh}"


class TestSpanishLabels:
    """Test extraction with Spanish anchor labels."""
    
    def test_spanish_labels_extraction(self, ensure_fixtures):
        """Should extract values from Spanish-labeled workbook."""
        workbook = read_fixture("secadora_spanish.xlsx")
        result = extract_required_inputs(workbook, "Secadora (SMG1234)")
        
        kwh = result.inputs.get("Use_kWh_per_year", 0)
        
        # "385,5" with European comma = 385.5
        assert 380 < kwh < 390, f"Spanish format should yield ~385.5, got {kwh}"


class TestModelSheetDetection:
    """Test automatic model sheet detection."""
    
    def test_detect_dryer_sheets(self):
        """Should detect dryer model sheets."""
        sheets = ["Summary", "Dryer SMG (SMG6527)", "Dryer GTD (GTD42XXX)", "Data"]
        detected = detect_model_sheets(sheets)
        
        assert "Dryer SMG (SMG6527)" in detected
        assert "Dryer GTD (GTD42XXX)" in detected
        assert "Summary" not in detected
    
    def test_detect_cooling_sheets(self):
        """Should detect cooling/refrigerator sheets."""
        sheets = ["Cover", "Cooling Unit (GSS25XXX)", "Raw Data"]
        detected = detect_model_sheets(sheets)
        
        assert "Cooling Unit (GSS25XXX)" in detected


# ============================================================================
# Smoke Test for Full Workflow
# ============================================================================

class TestFullWorkflow:
    """End-to-end workflow test."""
    
    def test_full_extraction_and_kpi(self, ensure_fixtures):
        """Complete workflow: extract -> compute KPIs -> verify differences."""
        # Load workbooks
        dryer_wb = read_fixture("dryer_workbook.xlsx")
        fridge_wb = read_fixture("refrigerator_workbook.xlsx")
        
        # Extract from different sheets/workbooks
        scenarios = [
            ("dryer_workbook.xlsx", "Dryer SMG (SMG6527)", dryer_wb),
            ("dryer_workbook.xlsx", "Dryer GTD (GTD42XXX)", dryer_wb),
            ("refrigerator_workbook.xlsx", "Cooling Unit (GSS25XXX)", fridge_wb),
        ]
        
        results = []
        for workbook_name, sheet_name, wb_bytes in scenarios:
            extraction = extract_required_inputs(wb_bytes, sheet_name)
            kpis = compute_kpis(extraction.inputs, grid_factor=0.25, lifetime=10)
            
            results.append({
                "workbook": workbook_name,
                "sheet": sheet_name,
                "Use_kWh_per_year": extraction.inputs.get("Use_kWh_per_year", 0),
                "Total_CO2e": kpis["Total_CO2e"],
                "provenance": extraction.provenance.get("Use_kWh_per_year"),
            })
        
        # Print results table for verification
        print("\n" + "=" * 80)
        print("EXTRACTION RESULTS:")
        print("=" * 80)
        for r in results:
            prov = r["provenance"]
            prov_str = f"{prov.method}:{prov.cell_ref}" if prov else "N/A"
            print(f"{r['workbook']:30} | {r['sheet']:25} | kWh={r['Use_kWh_per_year']:>7.1f} | Total CO2e={r['Total_CO2e']:>8.2f} | {prov_str}")
        print("=" * 80)
        
        # Verify all values are different
        kwh_values = [r["Use_kWh_per_year"] for r in results]
        assert len(set(kwh_values)) == 3, "All three scenarios should have different kWh values"
        
        total_values = [r["Total_CO2e"] for r in results]
        assert len(set(total_values)) == 3, "All three scenarios should have different totals"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
