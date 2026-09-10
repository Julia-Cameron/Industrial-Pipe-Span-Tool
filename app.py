import streamlit as st
import sqlite3
import math
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Page Configuration
st.set_page_config(page_title="Pipe Span & Support Engine", page_icon="⚙️", layout="wide")

st.title("⚙️ Industrial Pipe Span & Support Engineering Tool")
st.markdown("**Co-op Portfolio Project** | Built with Python, SQLite, and Streamlit following Oil & Gas standards.")

# Database Connection Helper
def get_db_connection():
    conn = sqlite3.connect("pipe_span_app.db")
    conn.row_factory = sqlite3.Row
    return conn

# Load dropdown data from SQLite
conn = get_db_connection()
pipes = conn.execute("SELECT * FROM pipes").fetchall()
fluids = conn.execute("SELECT * FROM fluids").fetchall()
zoning = conn.execute("SELECT * FROM canadian_zoning").fetchall()
conn.close()

# Sidebar Layout for Inputs
st.sidebar.header("🔧 Design Parameters")

pipe_options = {p["nps"]: p for p in pipes}
selected_nps = st.sidebar.selectbox("Select Nominal Pipe Size (NPS)", list(pipe_options.keys()))
chosen_pipe = pipe_options[selected_nps]

fluid_options = {f["fluid_name"]: f["density_kg_m3"] for f in fluids}
selected_fluid = st.sidebar.selectbox("Select Process Fluid", list(fluid_options.keys()))
fluid_density = fluid_options[selected_fluid]

insulation_weight = st.sidebar.number_input("Insulation Weight (kg/m)", min_value=0.0, value=3.2, step=0.5)
selected_zone = st.sidebar.selectbox("Canadian Environmental Region (NBC)", [z["region"] for z in zoning])

conn = get_db_connection()
zone_data = conn.execute("SELECT * FROM canadian_zoning WHERE region = ?", (selected_zone,)).fetchone()
conn.close()

# Main Dashboard Display
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Selected Pipe & Fluid Specifications")
    st.metric(label="Outer Diameter (OD)", value=f"{chosen_pipe['outer_diameter_mm']} mm")
    st.metric(label="Wall Thickness", value=f"{chosen_pipe['wall_thickness_mm']} mm")
    st.metric(label="Bare Pipe Weight", value=f"{chosen_pipe['weight_kg_m']} kg/m")
    st.metric(label="Fluid Density", value=f"{fluid_density} kg/m³")

with col2:
    st.subheader("🌦️ Environmental Zoning (NBC Standards)")
    st.metric(label="Wind Pressure (Qs)", value=f"{zone_data['wind_pressure_kpa']} kPa")
    st.metric(label="Snow / Ice Load", value=f"{zone_data['snow_load_kpa']} kPa")
    st.metric(label="Seismic Zone Factor", value=f"{zone_data['seismic_zone_factor']}")

st.markdown("---")

# Official ASME B31.1 Table 121.5 Baseline Spans (Water Service) & Interpolations
standard_spans_reference = {
    "1\"": 2.1,
    "2\"": 3.0,
    "3\"": 3.7,
    "4\"": 4.3,
    "6\"": 5.2,
    "8\"": 5.8,
    "12\"": 7.0,
    "16\"": 8.2,
    "24\"": 9.8
}

def get_code_baseline(nps):
    """Safely retrieves official ASME B31.1 code baseline or handles intermediate sizes via interpolation."""
    if nps in standard_spans_reference:
        return standard_spans_reference[nps]
    # Engineering fallback / interpolation approximation for unlisted intermediate sizes
    interpolations = {"1.5\"": 2.5, "10\"": 6.4, "10\"": 6.4}
    return interpolations.get(nps, 6.0)

# Calculation Logic Button
if st.button("Calculate Maximum Allowable Span & Supports", type="primary"):
    od = chosen_pipe["outer_diameter_mm"] / 1000.0
    wt = chosen_pipe["wall_thickness_mm"] / 1000.0
    id_pipe = od - (2 * wt)
    
    fluid_area = math.pi * (id_pipe / 2)**2
    fluid_weight_distributed = fluid_area * fluid_density
    
    ice_load_equivalent = zone_data["snow_load_kpa"] * 5.0 
    total_distributed_weight = chosen_pipe["weight_kg_m"] + fluid_weight_distributed + insulation_weight + ice_load_equivalent
    total_load_n_m = total_distributed_weight * 9.81
    
    z_modulus = (math.pi * (od**4 - id_pipe**4)) / (32 * od)
    moment_of_inertia = (math.pi * (od**4 - id_pipe**4)) / 64
    E_modulus = 200e9 
    allowable_stress = 20_000_000 
    
    if total_load_n_m > 0:
        span_stress = math.sqrt((8 * allowable_stress * z_modulus) / total_load_n_m)
        max_allowable_sag = 0.0025 
        span_deflection = ((384 * E_modulus * moment_of_inertia * max_allowable_sag) / (5 * total_load_n_m)) ** 0.25
        max_span_m = min(span_stress, span_deflection)
    else:
        max_span_m = 0.0

    max_span_m = round(max_span_m, 2)
    std_code_limit = get_code_baseline(selected_nps)
    is_compliant = max_span_m <= std_code_limit

    st.session_state['calc_results'] = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nps": selected_nps,
        "fluid": selected_fluid,
        "region": selected_zone,
        "total_weight": round(total_distributed_weight, 2),
        "calculated_span": max_span_m,
        "standard_span": std_code_limit,
        "od": chosen_pipe['outer_diameter_mm'],
        "wt": chosen_pipe['wall_thickness_mm'],
        "fluid_density": fluid_density,
        "insulation_weight": insulation_weight,
        "wind_pressure": zone_data['wind_pressure_kpa'],
        "snow_load": zone_data['snow_load_kpa'],
        "seismic": zone_data['seismic_zone_factor'],
        "is_compliant": is_compliant
    }

# Function to generate a clean, formatted PDF using ReportLab
def create_pdf_report(res):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor("#1f4e79"), spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.HexColor("#595959"), spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'SectionHeading', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor("#1f4e79"), spaceBefore=12, spaceAfter=6
    )
    normal_style = ParagraphStyle('NormalText', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=colors.HexColor("#262626"), leading=12)
    bold_style = ParagraphStyle('BoldText', parent=normal_style, fontName='Helvetica-Bold')

    # Title Banner Block
    story.append(Paragraph("INDUSTRIAL PIPE SPAN & SUPPORT REPORT", title_style))
    story.append(Paragraph(f"Generated on: {res['timestamp']} | Co-op Portfolio Engineering Tool", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1f4e79"), spaceAfter=10))

    # Section 1: Inputs Table
    story.append(Paragraph("1. Design Input Parameters", heading_style))
    input_data = [
        [Paragraph("<b>Parameter</b>", normal_style), Paragraph("<b>Value & Unit</b>", normal_style), Paragraph("<b>Parameter</b>", normal_style), Paragraph("<b>Value & Unit</b>", normal_style)],
        [Paragraph("Nominal Pipe Size (NPS)", normal_style), Paragraph(str(res['nps']), normal_style), Paragraph("Process Fluid", normal_style), Paragraph(str(res['fluid']), normal_style)],
        [Paragraph("Outer Diameter (OD)", normal_style), Paragraph(f"{res['od']} mm", normal_style), Paragraph("Fluid Density", normal_style), Paragraph(f"{res['fluid_density']} kg/m³", normal_style)],
        [Paragraph("Wall Thickness", normal_style), Paragraph(f"{res['wt']} mm", normal_style), Paragraph("Insulation Weight", normal_style), Paragraph(f"{res['insulation_weight']} kg/m", normal_style)],
        [Paragraph("NBC Region", normal_style), Paragraph(str(res['region']), normal_style), Paragraph("Wind / Snow / Seismic", normal_style), Paragraph(f"{res['wind_pressure']} / {res['snow_load']} / {res['seismic']} kPa", normal_style)]
    ]
    t1 = Table(input_data, colWidths=[130, 140, 130, 130])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f2f2f2")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#d9d9d9"))
    ]))
    story.append(t1)
    story.append(Spacer(1, 10))

   # Section 2: Results Table
    story.append(Paragraph("2. Span & Load Calculation Summary", heading_style))
    result_data = [
        [Paragraph("<b>Metric Description</b>", normal_style), Paragraph("<b>Computed Value</b>", normal_style), Paragraph("<b>Standard Code Baseline</b>", normal_style)],
        [Paragraph("Total Distributed Design Load", normal_style), Paragraph(f"{res['total_weight']} kg/m", normal_style), Paragraph("N/A", normal_style)],
        [Paragraph("Calculated Maximum Allowable Span", normal_style), Paragraph(f"<b>{res['calculated_span']} meters</b>", normal_style), Paragraph(f"{res['standard_span']} meters", normal_style)],
        [Paragraph("Code Compliance Status", normal_style), Paragraph(f"<b>{'COMPLIANT' if res['is_compliant'] else 'REVIEW REQUIRED'}</b>", normal_style), Paragraph("ASME B31.1 / MSS SP-69", normal_style)]
    ]
    t2 = Table(result_data, colWidths=[200, 150, 180])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f2f2f2")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#d9d9d9"))
    ]))
    story.append(t2)
    story.append(Spacer(1, 10))

    # Section 3: Recommendations & Engineering Basis
    story.append(Paragraph("3. Engineering Basis, Compliance & Recommendations", heading_style))
    rec_text = (
        "<b>Engineering Source Documentation:</b> Industry standard baselines are referenced from "
        "<b>ASME B31.1 (Table 121.5)</b> and <b>MSS SP-69</b> guidelines for standard-weight carbon steel piping "
        "in liquid service, assuming a maximum allowable mid-span deflection limit of 2.5 mm (0.1 in).<br/><br/>"
        "<b>Code Review Assessment:</b> " + ("The calculated maximum span complies securely with standard engineering baseline thresholds." if res['is_compliant'] else "The calculated span exceeds typical standard guidelines. Intermittent support re-evaluation is advised.") + "<br/><br/>" +
        "<b>Suggested Pipe Support Configuration:</b> " + ("Rigid Shoe Support with a Slide Plate to accommodate thermal expansion, coupled with a line stop or guide near high-load zones/valves." if res['calculated_span'] > 6.0 else "Standard Clevis Hanger or Adjustable Pipe Stand assembly is appropriate for this load class.")
    )
    story.append(Paragraph(rec_text, normal_style))
    story.append(Spacer(1, 20))

    # Footer Sign-off
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#d9d9d9"), spaceAfter=6))
    story.append(Paragraph("<i>Report generated automatically via Streamlit Python Pipeline. Certified for Portfolio Evaluation.</i>", subtitle_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# Display results if calculation has been executed
if 'calc_results' in st.session_state:
    res = st.session_state['calc_results']
    
    st.success("Calculation Completed Successfully!")
    
    res_col1, res_col2, res_col3 = st.columns(3)
    res_col1.metric(label="Total Distributed Load", value=f"{res['total_weight']} kg/m")
    res_col2.metric(label="Calculated Max Span", value=f"{res['calculated_span']} meters")
    res_col3.metric(label="Industry Standard Baseline", value=f"{res['standard_span']} meters")
    
    st.subheader("📊 Comparison with Canadian / Industry Standards")
    diff = round(res['calculated_span'] - res['standard_span'], 2)
    if res['is_compliant']:
        st.markdown(f"✅ **Code Compliance Check:** Passed. Your calculated span ({res['calculated_span']}m) is **within or equal to** the standard maximum guideline limit ({res['standard_span']}m) for size {res['nps']}.")
    else:
        st.warning(f"⚠️ **Code Compliance Review:** The calculated span ({res['calculated_span']}m) exceeds the typical standard baseline limit ({res['standard_span']}m) by {diff}m. Re-evaluate support spacing or add intermediate supports.")

    st.subheader("🛠️ Suggested Pipe Support Configuration")
    if res['calculated_span'] > 6.0:
        st.info("**Recommendation:** Use a **Rigid Shoe Support with a Slide Plate** to accommodate thermal expansion, coupled with a line stop or guide near heavy valves.")
    else:
         st.info("**Recommendation:** Standard **Clevis Hanger or Adjustable Pipe Stand** is sufficient for this load class.")

    st.markdown("---")
    st.subheader("📥 Export Engineering Report")
    
    pdf_bytes = create_pdf_report(res)

    st.download_button(
        label="📄 Download Formatted Engineering Report (.pdf)",
        data=pdf_bytes,
        file_name=f"Pipe_Span_Report_{res['nps'].replace('\"', 'in')}.pdf",
        mime="application/pdf"
    )