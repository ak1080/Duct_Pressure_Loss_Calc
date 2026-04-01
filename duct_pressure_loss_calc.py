from math import pi
from fluid_equations import reynolds_num, darcy_weisbach_pressure_loss
from fittings import (
    ASHRAE_CD3_12_Elbow, ASHRAE_CD3_17_Elbow, ASHRAE_CD9_1_Butterfly_Damper,
    ASHRAE_CR3_6_MiteredElbow, ASHRAE_CR3_1_SmoothRadiusElbow, ASHRAE_CR3_12_MiteredElbow,
    ASHRAE_ER5_2_Tee, ASHRAE_ER5_3_Tee, SMACNA_SmoothRadiusElbow, SMACNA_Rectangular_Z_Elbow,
    SMACNA_Converging_Tee_Round, SMACNA_Conical_Tee_Round, SMACNA_Rectangular_Main_Conical_Branch,
)

# ============================
# Fittings Catalog
# ============================
FITTINGS = {
    "1": ("ASHRAE CD3-12 3 Gore Elbow, Round (r/D = 0.75 to 2.0)", ASHRAE_CD3_12_Elbow),
    "2": ("ASHRAE CD3-17 45° Mitered Elbow, Round", ASHRAE_CD3_17_Elbow),
    "3": ("ASHRAE CD9-1 Butterfly Damper", ASHRAE_CD9_1_Butterfly_Damper),
    "4": ("ASHRAE CR3-1 Smooth Radius Elbow, Rect., No Vanes", ASHRAE_CR3_1_SmoothRadiusElbow),
    "5": ("ASHRAE CR3-6 Mitered Elbow No Vanes, Rect.", ASHRAE_CR3_6_MiteredElbow),
    "6": ("ASHRAE CR3-12 Mitered Elbow Single Vanes, Rect.", ASHRAE_CR3_12_MiteredElbow),
    "7": ("ASHRAE ER5-2 Tee, Round Branch into Rect. Main (Converging)", ASHRAE_ER5_2_Tee),
    "8": ("ASHRAE ER5-3 Tee, Rect. Branch into Rect. Main (Converging)", ASHRAE_ER5_3_Tee),
    "9": ("SMACNA Smooth Radius Elbow (Die Stamped)", SMACNA_SmoothRadiusElbow),
    "10": ("SMACNA Rectangular Z-Shaped Elbow", SMACNA_Rectangular_Z_Elbow),
    "11": ("SMACNA Converging Tee, 90° Round into Round Main", SMACNA_Converging_Tee_Round),
    "12": ("SMACNA Conical Tee, 90° Round out of Round Main", SMACNA_Conical_Tee_Round),
    "13": ("SMACNA Rectangular Main to Conical Supply Branch", SMACNA_Rectangular_Main_Conical_Branch),
}

# ============================
# Helper Functions
# ============================
def get_positive_number(prompt, number_type=float):
    """Prompt user until they enter a positive number."""
    while True:
        try:
            value = number_type(input(prompt))
            if value <= 0:
                raise ValueError
            return value
        except ValueError:
            print("Please enter a positive value.")

def add_duct_segment(index):
    shape = input("Duct shape ('round' or 'rect'): ").strip().lower()
    if shape == "round":
        diam = get_positive_number("Round duct diameter (in): ")
        desc = f'Round duct, Ø {diam:.2f}"'
    elif shape == "rect":
        w = get_positive_number("Duct width (in): ")
        h = get_positive_number("Duct height (in): ")
        diam = (1.30 * (w * h) ** 0.625) / (w + h) ** 0.25
        diam = round(diam, 3)
        desc = f'Rectangular duct, w: {w:.1f}", h: {h:.1f}", equiv. diam: {diam:.2f}"'
        print(f"Equivalent round diameter: {diam} in")
    else:
        print("Invalid duct shape.")
        return None

    cfm = get_positive_number("Airflow (CFM): ")
    length = get_positive_number("Duct length (ft): ")

    area_sqft = pi / 4 * (diam / 12) ** 2
    velocity = cfm / area_sqft
    reynolds = reynolds_num(velocity=velocity, diam=diam)
    loss = darcy_weisbach_pressure_loss(re=reynolds, velocity=velocity, diam=diam, duct_length=length)

    segment = {
        "index": index,
        "type": "duct",
        "name": f"{desc}, {length:.1f} ft",
        "cfm": cfm,
        "velocity": velocity,
        "vp": (velocity / 4005) ** 2,
        "C": 0.0,
        "loss": loss
    }
    print(f"Velocity: {velocity:.1f} fpm")
    print(f"Duct pressure loss added: {loss:.4f} inWC")
    return segment

def add_fitting_segment(index):
    print("\nAvailable fittings:")
    for key, (name, _) in FITTINGS.items():
        print(f"{key}: {name}")
    choice = input("Select fitting: ").strip()
    if choice not in FITTINGS:
        print("Invalid fitting selection.")
        return None

    name, fitting_cls = FITTINGS[choice]
    try:
        fitting = fitting_cls.from_user_input()
        r = fitting.results()
    except ValueError as e:
        print(f"Error: {e}")
        return None

    # Build fitting description
    if hasattr(fitting, "diameter_in") and hasattr(fitting, "r_d"):
        name_with_size = f"{name}, Ø {fitting.diameter_in:.2f}\" D, r/D: {fitting.r_d}"
        if hasattr(fitting, "theta_deg"):
            name_with_size += f", θ: {fitting.theta_deg}°"
        # Compute CFM based on velocity for this path
        area_sqft = pi / 4 * (fitting.diameter_in / 12) ** 2
        cfm = r["velocity"] * area_sqft
    elif hasattr(fitting, "diameter_in"):
        name_with_size = f"{name}, Ø {fitting.diameter_in:.2f}\""
        area_sqft = pi / 4 * (fitting.diameter_in / 12) ** 2
        cfm = r["velocity"] * area_sqft
    elif hasattr(fitting, "width_in") and hasattr(fitting, "height_in"):
        W, H = fitting.width_in, fitting.height_in
        name_with_size = f'{name}, w: {W:.1f}", h: {H:.1f}"'
        if hasattr(fitting, "length_in"):
            name_with_size += f', L: {fitting.length_in:.1f}"'
        if hasattr(fitting, "r_w"):
            name_with_size += f", r/W: {fitting.r_w}"
        if hasattr(fitting, "theta_deg"):
            name_with_size += f", θ: {fitting.theta_deg}°"
        # Compute CFM from area
        area_sqft = (W / 12) * (H / 12)
        cfm = r["velocity"] * area_sqft
    elif hasattr(fitting, "dimensions"):
        dims = fitting.dimensions()
        if "main" in dims and "branch" in dims:
            main, branch = dims["main"], dims["branch"]
            main_str = f'w: {main["width_in"]:.1f}", h: {main["height_in"]:.1f}", CFM: {main["cfm"]:.0f}' \
                if main.get("shape") == "rectangular" else f'Ø {main["diameter_in"]:.2f}", CFM: {main["cfm"]:.0f}'
            branch_str = f'w: {branch["width_in"]:.1f}", h: {branch["height_in"]:.1f}", CFM: {branch["cfm"]:.0f}' \
                if branch.get("shape") == "rectangular" else f'Ø {branch["diameter_in"]:.2f}", CFM: {branch["cfm"]:.0f}'
            name_with_size = f"{name}, main: {main_str}, branch: {branch_str}"
            # Determine which path was used for velocity in r["velocity"]
            path_key = r.get("flow_path", "").lower()
            if "main" in path_key:
                if main.get("shape") == "rectangular":
                    area_sqft = (main["width_in"] / 12) * (main["height_in"] / 12)
                else:
                    area_sqft = pi / 4 * (main["diameter_in"] / 12) ** 2
            elif "branch" in path_key:
                if branch.get("shape") == "rectangular":
                    area_sqft = (branch["width_in"] / 12) * (branch["height_in"] / 12)
                else:
                    area_sqft = pi / 4 * (branch["diameter_in"] / 12) ** 2
            else:
                # fallback to total CFM if unknown path
                cfm = getattr(fitting, "cfm", 0)
            cfm = r["velocity"] * area_sqft
        else:
            name_with_size = name
            cfm = getattr(fitting, "cfm", 0)
    else:
        name_with_size = name
        cfm = getattr(fitting, "cfm", 0)

    segment = {
        "index": index,
        "type": "fitting",
        "name": name_with_size,
        "flow_path": r.get("flow_path", ""),
        "cfm": cfm,
        "velocity": r["velocity"],
        "vp": r["vp"],
        "C": r["C"],
        "loss": r["loss"],
    }

    print(f"Velocity: {r['velocity']:.0f} fpm")
    print(f"CFM: {cfm:.0f}")
    print(f"Velocity pressure: {r['vp']:.4f} inWC")
    print(f"Loss coefficient C: {r['C']:.3f}")
    print(f"Fitting loss added: {r['loss']:.4f} inWC")
    return segment

def add_known_loss_segment(index):
    name = input("Enter description of loss (ex. flex duct, grille, etc.): ")
    loss = get_positive_number("Enter the known loss in inWC: ")
    print(f"Known loss added: {loss:.4f} inWC")
    return {
        "index": index,
        "type": "known",
        "name": name,
        "cfm": None,
        "velocity": 0.0,
        "vp": 0.0,
        "C": 0.0,
        "loss": loss
    }

def wrap_text(text, width):
    """Wrap long text for summary table."""
    if not text:
        return [""]
    lines = []
    while len(text) > width:
        split_at = text.rfind(" ", 0, width)
        if split_at == -1:
            split_at = width
        lines.append(text[:split_at])
        text = text[split_at:].lstrip()
    lines.append(text)
    return lines

def print_summary(components):
    # Column widths
    IDX_W, TYPE_W, FLOW_W, NAME_W, CFM_W, VEL_W, VP_W, C_W, LOSS_W = 4, 10, 30, 60, 10, 10, 10, 10, 12
    total_width = IDX_W + TYPE_W + FLOW_W + NAME_W + CFM_W + VEL_W + VP_W + C_W + LOSS_W + 8

    print("\nPRESSURE LOSS SUMMARY")
    print("=" * total_width)
    print(f"{'#':<{IDX_W}} {'Type':<{TYPE_W}} {'Flow Path':<{FLOW_W}} {'Component':<{NAME_W}} "
          f"{'CFM':>{CFM_W}} {'Vel(fpm)':>{VEL_W}} {'VP(inWC)':>{VP_W}} {'C':>{C_W}} {'Loss(inWC)':>{LOSS_W}}")
    print("-" * total_width)

    total_loss = 0.0
    for c in components:
        total_loss += c.get("loss", 0)
        cfm_str = f"{c['cfm']:.0f}" if c.get("cfm") else ""
        flow_str = c.get("flow_path", "")
        name_lines = wrap_text(c["name"], NAME_W)
        for i, line in enumerate(name_lines):
            print(f"{c['index'] if i==0 else '':<{IDX_W}} "
                  f"{c['type'] if i==0 else '':<{TYPE_W}} "
                  f"{flow_str if i==0 else '':<{FLOW_W}} "
                  f"{line:<{NAME_W}} "
                  f"{cfm_str if i==0 else '':>{CFM_W}} "
                  f"{f'{c["velocity"]:.0f}' if i==0 else '':>{VEL_W}} "
                  f"{f'{c["vp"]:.4f}' if i==0 else '':>{VP_W}} "
                  f"{f'{c["C"]:.3f}' if i==0 else '':>{C_W}} "
                  f"{f'{c["loss"]:.4f}' if i==0 else '':>{LOSS_W}}")
    print("-" * total_width)
    print(f"{'TOTAL PRESSURE LOSS':<{total_width - LOSS_W}} {total_loss:>{LOSS_W}.4f}")

# ============================
# Main Program
# ============================
def main():
    components = []
    index = 1

    while True:
        element = input("\nAdd element ('duct', 'fitting', 'known', or 'done'): ").strip().lower()
        if element == "done":
            break
        if element == "duct":
            segment = add_duct_segment(index)
        elif element == "fitting":
            segment = add_fitting_segment(index)
        elif element == "known":
            segment = add_known_loss_segment(index)
        else:
            print("Invalid option. Please enter 'duct', 'fitting', 'known', or 'done'.")
            continue

        if segment:
            components.append(segment)
            index += 1

    print_summary(components)

if __name__ == "__main__":
    main()
