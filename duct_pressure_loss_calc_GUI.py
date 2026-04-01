import streamlit as st
from math import pi
import pandas as pd
from pathlib import Path
import io
import uuid
import json


PROJECTS_DIR = Path(__file__).parent / "projects"
PROJECTS_DIR.mkdir(exist_ok=True)

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from fluid_equations import reynolds_num, darcy_weisbach_pressure_loss
from fittings import (
    ASHRAE_CD3_12_Elbow, ASHRAE_CD3_17_Elbow, ASHRAE_CD9_1_Butterfly_Damper,
    ASHRAE_CR3_6_MiteredElbow, ASHRAE_CR3_1_SmoothRadiusElbow, ASHRAE_CR3_12_MiteredElbow,
    ASHRAE_ER5_2_Tee, ASHRAE_ER5_3_Tee,
    SMACNA_SmoothRadiusElbow,
    SMACNA_Rectangular_Z_Elbow,
    SMACNA_Converging_Tee_Round,
    SMACNA_Conical_Tee_Round,
    SMACNA_Rectangular_Main_Conical_Branch,
)


PROJECTS_FOLDER = Path(__file__).parent / "projects"
PROJECTS_FOLDER.mkdir(exist_ok=True)

def choose_project_file(project_name: str) -> Path | None:
    """
    Return the full path to a project JSON file in the projects folder.
    If the project does not exist, return None.
    """
    if not project_name:
        return None

    file_path = PROJECTS_FOLDER / f"{project_name}.json"
    if file_path.exists():
        return file_path
    else:
        return None

def load_project(project_name):
    file_path = PROJECTS_FOLDER / f"{project_name}.json"

    if not file_path.exists():
        st.error("Project not found.")
        return

    with open(file_path, "r") as f:
        data = json.load(f)

    st.session_state.components = data.get("components", [])
    st.session_state.system_name = data.get("system_name", "")
    st.session_state.current_project = data.get("project_name", "")

    st.success(f"Loaded project: {project_name}")


##########################################################################

st.markdown("""
<style>

.fitting-card {
    border: 2px solid #d9d9d9;
    border-radius: 10px;
    padding: 15px;
    display: flex;
    flex-direction: column;
    align-items: center;
    background-color: white;
    transition: 0.2s ease;
}

.fitting-card.selected {
    border-color: #28a745;
    box-shadow: 0 0 8px rgba(40,167,69,0.35);
}

.fitting-card:hover {
    border-color: #007acc;
    transform: translateY(-3px);
}

.fitting-img {
    width: 100%;
    height: 240px;
    display: flex;
    justify-content: center;
    align-items: center;
}

.fitting-img img {
    max-height: 220px;
    max-width: 100%;
    object-fit: contain;
}

.fitting-title {
    text-align: center;
    font-weight: 600;
    font-size: 0.9rem;
    min-height: 50px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.stButton > button {
    width: 100%;
}

</style>
""", unsafe_allow_html=True)


st.set_page_config(layout="wide")


# =====================================================
# FITTINGS CATALOG
# =====================================================
FITTINGS = {
    "1": ("ASHRAE CD3-12 3 Gore Elbow, Round", ASHRAE_CD3_12_Elbow),
    "2": ("ASHRAE CD3-17 45° Mitered Elbow, Round", ASHRAE_CD3_17_Elbow),
    "3": ("ASHRAE CD9-1 Butterfly Damper", ASHRAE_CD9_1_Butterfly_Damper),
    "4": ("ASHRAE CR3-1 Smooth Radius Elbow, Rect.", ASHRAE_CR3_1_SmoothRadiusElbow),
    "5": ("ASHRAE CR3-6 Mitered Elbow no Vanes, Rect.", ASHRAE_CR3_6_MiteredElbow),
    "6": ("ASHRAE CR3-12 Mitered Elbow w/ Vanes, Rect.", ASHRAE_CR3_12_MiteredElbow),
    "7": ("ASHRAE ER5-2 Tee, Round Branch into Rect Main", ASHRAE_ER5_2_Tee),
    "8": ("ASHRAE ER5-3 Tee, Rect Branch into Rect Main", ASHRAE_ER5_3_Tee),
    "9": ("SMACNA Smooth Radius Elbow", SMACNA_SmoothRadiusElbow),
    "10": ("SMACNA Rectangular Z-Elbow", SMACNA_Rectangular_Z_Elbow),
    "11": ("SMACNA Converging Tee, Round", SMACNA_Converging_Tee_Round),
    "12": ("SMACNA Conical Tee, Round", SMACNA_Conical_Tee_Round),
    "13": ("SMACNA Rectangular to Conical Branch", SMACNA_Rectangular_Main_Conical_Branch),
}

# =====================================================
# FITTING INPUT DEFINITIONS
# =====================================================
FITTING_INPUTS = {
    "1": [("diameter_in", "number", 12), ("r_d", "select", [0.75, 1.0, 1.5, 2.0])],
    "2": [("diameter_in", "number", 12)],
    "3": [("diameter_in", "number", 12)],
    "4": [
        ("width_in", "number", 12),
        ("height_in", "number", 12),
        ("r_w", "select", [0.5, 0.75, 1.0, 1.5, 2.0]),
        ("theta_deg", "select", [30, 45, 60, 90, 110, 130, 150, 180]),
    ],
    "5": [
        ("width_in", "number", 12),
        ("height_in", "number", 12),
        ("theta_deg", "select", [30, 45, 60, 75, 90]),
    ],
    "6": [("width_in", "number", 12), ("height_in", "number", 12)],
    "7": [
        ("width_in", "number", 24),
        ("height_in", "number", 12),
        ("Qs (CFM)", "number", 1500),
        ("branch_diam_in", "number", 10),
        ("Qb (CFM)", "number", 500),
        ("flow_type", "select", ["main", "branch"]),
    ],
    "8": [
        ("width_in", "number", 24),
        ("height_in", "number", 12),
        ("Qs (CFM)", "number", 1500),
        ("branch_width_in", "number", 10),
        ("branch_height_in", "number", 8),
        ("Qb (CFM)", "number", 500),
        ("flow_type", "select", ["main", "branch"]),
    ],
    "9": [
        ("diameter_in", "number", 12),
        ("r_d", "select", [0.5, 0.75, 1.0, 1.5, 2.0]),
        ("theta_deg", "select", [30, 45, 60, 75, 90, 110, 130, 150, 180]),
    ],
    "10": [
        ("width_in", "number", 24),
        ("height_in", "number", 12),
        ("length_in", "number", 12),
    ],
    "11": [
        ("main_diam_in", "number", 24),
        ("Qs (CFM)", "number", 1500),
        ("branch_diam_in", "number", 12),
        ("Qb (CFM)", "number", 500),
        ("flow_type", "select", ["main", "branch"]),
    ],
    "12": [
        ("main_diam_in", "number", 24),
        ("Qc (CFM)", "number", 2000),
        ("branch_diam_in", "number", 12),
        ("Qb (CFM)", "number", 800),
        ("flow_type", "select", ["main", "branch"]),
    ],
    "13": [
        ("main_width_in", "number", 24),
        ("main_height_in", "number", 12),
        ("Qc (CFM)", "number", 2000),
        ("branch_diam_in", "number", 12),
        ("Qb (CFM)", "number", 800),
        ("flow_type", "select", ["main", "branch"]),
    ],
}

# =====================================================
# SESSION STATE
# =====================================================
if "components" not in st.session_state:
    st.session_state.components = []

if "selected_fitting" not in st.session_state:
    st.session_state.selected_fitting = None

if "current_project" not in st.session_state:
    st.session_state.current_project = ""

if "system_name" not in st.session_state:
    st.session_state.system_name = ""

# SAVE PROJECT
def save_project(project_name):
    if not project_name:
        st.error("Project name required.")
        return

    if not st.session_state.components:
        st.warning("No components to save.")
        return

    file_path = PROJECTS_FOLDER / f"{project_name}.json"

    data = {
        "project_name": project_name,
        "system_name": st.session_state.system_name,
        "components": st.session_state.components
    }

    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        st.success(f"Project saved to: {file_path}")

    except Exception as e:
        st.error(f"Error saving project: {e}")

# =====================================================
# PROJECT SIDEBAR
# =====================================================

st.sidebar.header("Projects")

# List existing project files
existing_projects = sorted([p.stem for p in PROJECTS_FOLDER.glob("*.json")])
selected_project = st.sidebar.selectbox("Open Project", [""] + existing_projects)

col1, col2 = st.sidebar.columns(2)

if col1.button("Load"):
    if selected_project:
        load_project(selected_project)
    else:
        st.sidebar.warning("Select a project to load.")

if col2.button("New"):
    st.session_state.components = []
    st.session_state.system_name = ""
    st.session_state.current_project = ""
    st.success("New project started.")

st.sidebar.markdown("---")

# Save project
project_to_save = st.sidebar.text_input("Project Name", value=st.session_state.current_project)
if st.sidebar.button("Save Project"):
    save_project(project_to_save)


# -----------------------------------------------------
# List Projects in Folder
# -----------------------------------------------------
existing_projects = sorted([p.stem for p in PROJECTS_FOLDER.glob("*.json")])


PROJECTS_FOLDER = Path(__file__).parent / "projects"
PROJECTS_FOLDER.mkdir(exist_ok=True)


# =====================================================
# UI
# =====================================================
st.title("Duct Pressure Loss Calculator")
element_type = st.selectbox("Select element to add", ["Duct", "Fitting", "Known"])

# =====================================================
# DUCT
# =====================================================
if element_type == "Duct":
    st.subheader("Add Duct")
    shape = st.selectbox("Duct shape", ["round", "rectangular"])

    if shape == "round":
        diam = st.number_input("Diameter (in)", min_value=1, value=12, step=1)
    else:
        w = st.number_input("Width (in)", min_value=1, value=12, step=1)
        h = st.number_input("Height (in)", min_value=1, value=12, step=1)

    cfm = st.number_input("Airflow (CFM)", min_value=1, value=1000, step=1)
    length = st.number_input("Length (ft)", min_value=1, value=10, step=1)

    if st.button("Add Duct"):
        if shape == "round":
            diam_eq = diam
            desc = f'Round duct, Ø {diam_eq:.2f}"'
        else:
            diam_eq = (1.30 * (w * h) ** 0.625) / (w + h) ** 0.25
            desc = f'Rect duct, w: {w:.1f}", h: {h:.1f}", eq Ø {diam_eq:.2f}"'

        area = pi / 4 * (diam_eq / 12) ** 2
        velocity = cfm / area
        re = reynolds_num(velocity, diam_eq)
        loss = darcy_weisbach_pressure_loss(re, velocity, diam_eq, length)

        st.session_state.components.append({
            "id": str(uuid.uuid4()),
            "type": "duct",
            "name": f"{desc}, {length:.1f} ft",
            "cfm": cfm,
            "velocity": velocity,
            "vp": (velocity / 4005) ** 2,
            "C": 0.0,
            "loss": loss,
        })



# =====================================================
# FITTING
# =====================================================
elif element_type == "Fitting":

    st.subheader("Select Fitting by Image")
    BASE_DIR = Path(__file__).parent
    image_folder = BASE_DIR / "fitting_images"

    # -----------------------------
    # Display fittings in 3 columns per row with larger images
    # -----------------------------
    fittings_list = list(FITTINGS.items())
    num_cols = 3  # number of cards per row
    image_width = 360  # larger image width

    for i in range(0, len(fittings_list), num_cols):
        row_items = fittings_list[i:i + num_cols]
        cols = st.columns(num_cols)

        for col, (idx, (fitting_name, _)) in zip(cols, row_items):
            image_path = image_folder / f"fitting_{idx}.png"
            is_selected = st.session_state.selected_fitting == str(idx)

            with col:
                # Start card container
                st.markdown(
                    f'<div class="fitting-card {"selected" if is_selected else ""}">',
                    unsafe_allow_html=True
                )

                # Image container + image
                import base64

                if image_path.exists():
                    with open(image_path, "rb") as img_file:
                        encoded = base64.b64encode(img_file.read()).decode()

                    st.markdown(
                        f"""
                        <div class="fitting-img">
                            <img src="data:image/png;base64,{encoded}" />
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.warning("Image missing")

                # Fitting name/title
                st.markdown(
                    f'<div class="fitting-title">{fitting_name}</div>',
                    unsafe_allow_html=True
                )

                # Select button aligned at bottom
                if st.button("Select", key=f"fitting_btn_{idx}", use_container_width=True):
                    st.session_state.selected_fitting = str(idx)

                # End card container
                st.markdown('</div>', unsafe_allow_html=True)

    # -----------------------------
    # Show inputs for selected fitting
    # -----------------------------
    if st.session_state.selected_fitting:
        selected_fitting = st.session_state.selected_fitting
        base_name, cls = FITTINGS[selected_fitting]

        st.markdown("---")
        st.markdown(f"### Enter Inputs for: {base_name}")

        input_cols = st.columns([1, 2])

        image_path = image_folder / f"fitting_{selected_fitting}.png"
        if image_path.exists():
            input_cols[0].image(image_path, width=image_width)
        else:
            input_cols[0].markdown("⚠️ Image not found.")

        inputs = {}
        for name, kind, default in FITTING_INPUTS.get(selected_fitting, []):
            if kind == "number":
                inputs[name] = input_cols[1].number_input(
                    name, min_value=1, value=int(default), step=1
                )
            elif kind == "select":
                options = default
                inputs[name] = input_cols[1].selectbox(name, options, index=0)

        # Non-special fittings: allow CFM input
        if selected_fitting not in ("7", "8", "11", "12", "13"):
            inputs["cfm"] = input_cols[1].number_input(
                "Airflow (CFM)", min_value=1, value=1000
            )

        # Validation for special fittings
        if selected_fitting in ("11", "12"):
            main_diam = inputs.get("main_diam_in")
            branch_diam = inputs.get("branch_diam_in")
            if branch_diam > main_diam:
                input_cols[1].error("Branch diameter cannot exceed main diameter.")
                st.stop()

        if input_cols[1].button("Add Fitting"):
            try:
                # Handle parameter renaming for special fittings
                PARAM_RENAME_MAP = {
                    "7": {"width_in": "main_width_in", "height_in": "main_height_in", "Qs (CFM)": "main_cfm",
                          "branch_diam_in": "branch_diam_in", "Qb (CFM)": "branch_cfm", "flow_type": "flow_type"},
                    "8": {"width_in": "main_width_in", "height_in": "main_height_in", "Qs (CFM)": "main_cfm",
                          "branch_width_in": "branch_width_in", "branch_height_in": "branch_height_in",
                          "Qb (CFM)": "branch_cfm", "flow_type": "flow_type"},
                    "11": {"main_diam_in": "main_diam_in", "Qs (CFM)": "Qs",
                           "branch_diam_in": "branch_diam_in", "Qb (CFM)": "Qb", "flow_type": "flow_type"},
                    "12": {"main_diam_in": "main_diam_in", "Qc (CFM)": "Qc",
                           "branch_diam_in": "branch_diam_in", "Qb (CFM)": "Qb", "flow_type": "flow_type"},
                    "13": {"main_width_in": "main_width_in", "main_height_in": "main_height_in", "Qc (CFM)": "Qc",
                           "branch_diam_in": "branch_diam_in", "Qb (CFM)": "Qb", "flow_type": "flow_type"},
                }

                renamed_inputs = PARAM_RENAME_MAP.get(selected_fitting, {})
                renamed_inputs = {renamed_inputs.get(k, k): v for k, v in inputs.items()}

                fitting = cls(**renamed_inputs)
                r = fitting.results()
                flow_path = r.get("flow_path", "").lower()



                name_with_size = base_name
                # --------------------------------------------------
                # Append basic size information for common fittings
                # -------------------------------------------------

                size_parts = []

                # Round diameter
                if hasattr(fitting, "diameter_in"):
                    size_parts.append(f'Ø {fitting.diameter_in:.2f}"')

                # Rectangular size
                if hasattr(fitting, "width_in") and hasattr(fitting, "height_in"):
                    size_parts.append(f'w: {fitting.width_in:.1f}", h: {fitting.height_in:.1f}"')

                # Z-Elbow length
                if hasattr(fitting, "length_in"):
                    size_parts.append(f'L {fitting.length_in:.1f}"')

                # Elbow angle
                if hasattr(fitting, "theta_deg"):
                    size_parts.append(f'θ {fitting.theta_deg}°')

                # Radius ratios
                if hasattr(fitting, "r_d"):
                    size_parts.append(f'R/D {fitting.r_d}')

                if hasattr(fitting, "r_w"):
                    size_parts.append(f'R/W {fitting.r_w}')

                # Tee geometry
                if hasattr(fitting, "main_diam_in"):
                    size_parts.append(f'Main Ø {fitting.main_diam_in:.2f}"')

                if hasattr(fitting, "branch_diam_in"):
                    size_parts.append(f'Branch Ø {fitting.branch_diam_in:.2f}"')

                if size_parts:
                    name_with_size = f"{base_name}, " + ", ".join(size_parts)
                cfm_calc = getattr(fitting, "cfm", None)

                velocity = r.get("velocity")
                vp = r.get("vp")
                loss = r.get("loss")
                C = r.get("C")

                # --------------------------------------------------
                # Special Case: ASHRAE ER5-2 and ER5-3 Tees
                # Main loss uses Qs, branch loss uses Qb
                # --------------------------------------------------
                if selected_fitting in ("7", "8"):

                    flow_type = renamed_inputs.get("flow_type")

                    if flow_type == "main":
                        cfm_calc = renamed_inputs.get("main_cfm")

                    elif flow_type == "branch":
                        cfm_calc = renamed_inputs.get("branch_cfm")
                # --------------------------------------------------
                # Special Case 1: SMACNA Conical Tee (12)
                # Based on upstream airflow Qc
                # --------------------------------------------------
                if selected_fitting == "12":

                    Qc = renamed_inputs.get("Qc")
                    main_diam = renamed_inputs.get("main_diam_in")

                    area_sqft = pi / 4 * (main_diam / 12) ** 2
                    velocity = Qc / area_sqft
                    vp = (velocity / 4005) ** 2
                    loss = C * vp

                    cfm_calc = Qc


                # --------------------------------------------------
                # Special Case 2: SMACNA Converging Tee (11)
                # ALWAYS use downstream airflow Qc = Qs + Qb
                # Coefficient C already reflects selected path
                # --------------------------------------------------
                elif selected_fitting == "11":

                    Qs = renamed_inputs.get("Qs")
                    Qb = renamed_inputs.get("Qb")
                    Qc = Qs + Qb

                    main_diam = renamed_inputs.get("main_diam_in")
                    area_sqft = pi / 4 * (main_diam / 12) ** 2

                    velocity = Qc / area_sqft
                    vp = (velocity / 4005) ** 2
                    loss = C * vp

                    cfm_calc = Qc


                # --------------------------------------------------
                # Other fittings (use class velocity result)
                # --------------------------------------------------
                elif hasattr(fitting, "diameter_in"):

                    area_sqft = pi / 4 * (fitting.diameter_in / 12) ** 2
                    cfm_calc = r["velocity"] * area_sqft


                elif hasattr(fitting, "width_in") and hasattr(fitting, "height_in"):

                    W, H = fitting.width_in, fitting.height_in
                    area_sqft = (W / 12) * (H / 12)
                    cfm_calc = r["velocity"] * area_sqft

                # --------------------------------------------------
                # Tee-style formatted description
                # --------------------------------------------------
                if hasattr(fitting, "dimensions"):

                    dims = fitting.dimensions()

                    if "main" in dims and "branch" in dims:
                        main, branch = dims["main"], dims["branch"]

                        main_str = (
                            f'w: {main["width_in"]:.1f}", h: {main["height_in"]:.1f}", CFM: {main["cfm"]:.0f}'
                            if main.get("shape") == "rectangular"
                            else f'Ø {main["diameter_in"]:.2f}", CFM: {main["cfm"]:.0f}'
                        )

                        branch_str = (
                            f'w: {branch["width_in"]:.1f}", h: {branch["height_in"]:.1f}", CFM: {branch["cfm"]:.0f}'
                            if branch.get("shape") == "rectangular"
                            else f'Ø {branch["diameter_in"]:.2f}", CFM: {branch["cfm"]:.0f}'
                        )

                        name_with_size = f"{base_name}, main: {main_str}, branch: {branch_str}"

                # --------------------------------------------------
                # Append to session state
                # --------------------------------------------------

                st.session_state.components.append({
                    "id": str(uuid.uuid4()),
                    "type": "fitting",
                    "name": name_with_size,
                    "flow_path": flow_path.capitalize(),
                    "cfm": cfm_calc,
                    "velocity": velocity,
                    "vp": vp,
                    "C": C,
                    "loss": loss,
                })

                st.success(f"Fitting added: {name_with_size} (Loss: {r.get('loss', 0):.4f} inWC)")
                st.session_state.selected_fitting = None

            except Exception as e:
                st.error(f"Error creating fitting: {e}")

# =====================================================
# KNOWN LOSS
# =====================================================
elif element_type == "Known":

    st.subheader("Add Known Loss")
    desc = st.text_input("Description")
    loss = st.number_input("Loss (inWC)", min_value=0.0, value=0.1)

    if st.button("Add Known Loss"):
        st.session_state.components.append({
            "id": str(uuid.uuid4()),
            "type": "known",
            "name": desc,
            "cfm": "",
            "velocity": 0.0,
            "vp": 0.0,
            "C": 0.0,
            "loss": loss,
        })


# =====================================================
# SUMMARY + PDF
# =====================================================
if st.session_state.components:

    # -----------------------------
    # System + Project Name
    # -----------------------------
    system_name = st.text_input(
        "System Name",
        value=st.session_state.system_name
    )

    st.session_state.system_name = system_name

    project_name = st.text_input(
        "Project Name",
        value=st.session_state.current_project
    )

    # Keep session state updated when user edits
    st.session_state.current_project = project_name

    author_credit = "Developed in Python by Alex Kalmbach"

    st.subheader(f"{system_name} Pressure Loss Summary")

    if project_name:
        st.markdown(f"**Project:** {project_name}")

    safety_factor_percent = st.number_input(
        "Safety Factor (%)", min_value=0, value=20, step=1
    )

    # Column widths for Streamlit layout
    column_widths = [0.7, 0.7, 1, 2, 5, 2, 2, 2, 2, 2, 2, 1, 1]

    headers = [
        "↑", "↓", "#", "Type", "Description", "Flow Path", "CFM",
        "Velocity (FPM)", "VP (inWC)", "C", "Loss (inWC)", "⧉", "Remove"
    ]

    header_cols = st.columns(column_widths)
    for col, label in zip(header_cols, headers):
        col.markdown(f"**{label}**")

    # -----------------------------
    # Display Table
    # -----------------------------
    for i, comp in enumerate(st.session_state.components):
        cols = st.columns(column_widths)
        row_number = i + 1
        if cols[0].button("⬆", key=f"up_{comp['id']}"):
            if i > 0:
                st.session_state.components[i], st.session_state.components[i - 1] = \
                    st.session_state.components[i - 1], st.session_state.components[i]
                st.rerun()
        if cols[1].button("⬇", key=f"down_{comp['id']}"):
            if i < len(st.session_state.components) - 1:
                st.session_state.components[i], st.session_state.components[i + 1] = \
                    st.session_state.components[i + 1], st.session_state.components[i]
                st.rerun()

        comp.setdefault("flow_path", "")
        comp.setdefault("cfm", None)
        comp.setdefault("velocity", None)
        comp.setdefault("vp", None)
        comp.setdefault("C", None)
        comp.setdefault("loss", None)

        cols[2].markdown(f"{row_number}")
        cols[3].markdown(comp["type"].capitalize())
        cols[4].markdown(comp["name"])
        cols[5].markdown(comp.get("flow_path", ""))
        cols[6].markdown(int(round(comp.get("cfm", 0))) if comp.get("cfm") else "")
        cols[7].markdown(int(round(comp.get("velocity", 0))) if comp.get("velocity") else "")
        cols[8].markdown(round(comp.get("vp", 0), 3) if comp.get("vp") else "")
        cols[9].markdown(round(comp.get("C", 0), 3) if comp.get("C") else "")
        cols[10].markdown(round(comp.get("loss", 0), 3) if comp.get("loss") else "")
        if cols[11].button("⧉", key=f"dup_{comp['id']}"):
            new_comp = comp.copy()
            new_comp["id"] = str(uuid.uuid4())

            st.session_state.components.insert(i + 1, new_comp)

            st.rerun()

        # -----------------------------
        # REMOVE BUTTON
        # -----------------------------
        if cols[12].button("❌", key=f"remove_{comp['id']}"):
            st.session_state.components = [
                c for c in st.session_state.components
                if c["id"] != comp["id"]
            ]
            st.rerun()

    # -----------------------------
    # Totals
    # -----------------------------
    total_loss = sum(c.get("loss", 0) for c in st.session_state.components)
    total_loss_with_sf = round(total_loss * (1 + safety_factor_percent / 100), 3)

    st.markdown(
        f"## TOTAL PRESSURE LOSS: {total_loss:.3f} inWC  \n"
        f"### With Safety Factor ({safety_factor_percent}%): {total_loss_with_sf:.2f} inWC"
    )

    # -----------------------------
    # Prepare DataFrame for PDF
    # -----------------------------
    df = pd.DataFrame(st.session_state.components).copy()
    df.insert(0, "#", range(1, len(df) + 1))

    numeric_cols = ["#", "cfm", "velocity", "vp", "C", "loss"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df_display = df.rename(columns={
        "type": "Type",
        "name": "Description",
        "flow_path": "Flow Path",
        "cfm": "CFM",
        "velocity": "Velocity (FPM)",
        "vp": "VP (inWC)",
        "C": "C",
        "loss": "Loss (inWC)"
    })[[
        "#", "Type", "Description", "Flow Path",
        "CFM", "Velocity (FPM)", "VP (inWC)", "C", "Loss (inWC)"
    ]]

    # -----------------------------
    # Decimal Control Per Column
    # -----------------------------
    column_decimals = {
        "#": 0,
        "CFM": 0,
        "Velocity (FPM)": 0,
        "VP (inWC)": 3,
        "C": 3,
        "Loss (inWC)": 3
    }

    # -----------------------------
    # PDF Generation
    # -----------------------------
    def create_pdf(dataframe, total_loss, total_loss_with_sf,
                   system_name, project_name, col_widths_pts=None):

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']

        # Title
        elements.append(Paragraph(f"{system_name} Pressure Loss Summary", styles['Title']))
        elements.append(Spacer(1, 6))

        # Project Name (if entered)
        if project_name:
            elements.append(Paragraph(f"<b>Project:</b> {project_name}", normal_style))
            elements.append(Spacer(1, 12))
        else:
            elements.append(Spacer(1, 12))

        dataframe_filled = dataframe.fillna("")

        data = [list(dataframe_filled.columns)]
        for row in dataframe_filled.values.tolist():
            new_row = []
            for col_index, item in enumerate(row):
                col_name = dataframe_filled.columns[col_index]

                if col_name == "Description":
                    new_row.append(Paragraph(str(item), normal_style))

                elif col_name in column_decimals:
                    decimals = column_decimals[col_name]
                    if isinstance(item, (float, int)):
                        new_row.append(f"{item:.{decimals}f}")
                    else:
                        new_row.append(str(item))

                else:
                    new_row.append(str(item))

            data.append(new_row)

        # Summary rows
        summary_row1 = [""] * len(dataframe_filled.columns)
        summary_row1[2] = "TOTAL PRESSURE LOSS:"
        summary_row1[8] = f"{total_loss:.3f} inWC"

        summary_row2 = [""] * len(dataframe_filled.columns)
        summary_row2[2] = f"With Safety Factor ({safety_factor_percent}%):"
        summary_row2[8] = f"{total_loss_with_sf:.2f} inWC"

        data.append(summary_row1)
        data.append(summary_row2)

        if not col_widths_pts:
            col_widths_pts = [30, 50, 150, 60, 50, 70, 60, 40, 60]

        t = Table(data, colWidths=col_widths_pts)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),
            ('BACKGROUND', (2, -2), (8, -1), colors.lightgrey),
        ]))

        elements.append(t)

        # Footer (Lower Right)
        def add_footer(canvas, doc):
            canvas.saveState()
            canvas.setFont("Helvetica", 8)
            canvas.drawRightString(letter[0] - 40, 25, author_credit)
            canvas.restoreState()

        doc.build(
            elements,
            onFirstPage=add_footer,
            onLaterPages=add_footer
        )

        buffer.seek(0)
        return buffer

    pdf_buffer = create_pdf(
        df_display,
        total_loss,
        total_loss_with_sf,
        system_name,
        project_name
    )

    st.download_button(
        "Download PDF",
        data=pdf_buffer,
        file_name=f"{system_name}_pressure_loss_summary.pdf",
        mime="application/pdf"
    )
