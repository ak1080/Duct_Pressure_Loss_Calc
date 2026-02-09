# fittings.py
from abc import ABC, abstractmethod
from math import pi

# ============================
# Base fitting class
# ============================

class Fitting(ABC):

    @classmethod
    @abstractmethod
    def from_user_input(cls):
        pass

    @abstractmethod
    def velocity_fpm(self):
        pass

    @abstractmethod
    def loss_coefficient(self):
        pass

    def velocity_pressure(self):
        v = self.velocity_fpm()
        return (v / 4005) ** 2

    def pressure_loss(self):
        return self.loss_coefficient() * self.velocity_pressure()

    def results(self):
        return {
            "velocity": self.velocity_fpm(),
            "vp": self.velocity_pressure(),
            "C": self.loss_coefficient(),
            "loss": self.pressure_loss()
        }

# ============================
# Helper functions
# ============================

def round_velocity(cfm, diameter_in):
    area_sqft = pi / 4 * (diameter_in / 12) ** 2
    return cfm / area_sqft

def rect_velocity(cfm, width_in, height_in):
    area_sqft = (width_in * height_in) / 144
    return cfm / area_sqft


# ============================
# CD3-12 3 Gore Elbow, Round (r/D = 0.75 to 2.0)
# ============================
class ASHRAE_CD3_12_Elbow(Fitting):

    C_TABLE = {0.75: 0.54, 1.00: 0.42, 1.50: 0.34, 2.00: 0.33}

    def __init__(self, diameter_in, r_d, cfm):
        self.diameter_in = diameter_in
        self.r_d = r_d
        self.cfm = cfm

    @classmethod
    def from_user_input(cls):
        # Select r/D ratio
        valid = sorted(cls.C_TABLE)
        # Get integer, positive duct diameter
        while True:
            try:
                d = int(input("Duct diameter (in): "))
                if d <= 0:
                    print("Diameter must be a positive integer.")
                    continue
                break
            except ValueError:
                print("Enter an integer value for diameter.")

        while True:
            try:
                print("Available r/D ratios:", ", ".join(map(str, valid)))
                r_d = float(input("r/D ratio: "))
                if r_d in cls.C_TABLE:
                    break
                print("Invalid r/D ratio. Choose from the list above.")
            except ValueError:
                print("Enter a numeric value.")

        # Get positive airflow
        while True:
            try:
                cfm = float(input("Airflow (CFM): "))
                if cfm <= 0:
                    print("Airflow must be positive.")
                    continue
                break
            except ValueError:
                print("Enter a numeric value.")

        return cls(d, r_d, cfm)

    def velocity_fpm(self):
        return round_velocity(self.cfm, self.diameter_in)

    def loss_coefficient(self):
        return self.C_TABLE[self.r_d]


# ============================
# CD3-17 45° Mitered Elbow, Round
# ============================
class ASHRAE_CD3_17_Elbow(Fitting):

    C_TABLE = {
        3: 0.87, 6: 0.79, 9: 0.74, 12: 0.72,
        15: 0.71, 18: 0.70, 21: 0.69, 24: 0.68, 27: 0.68, 60: 0.67
    }

    def __init__(self, diameter_in, cfm):
        self.diameter_in = diameter_in
        self.cfm = cfm

    @classmethod
    def from_user_input(cls):
        while True:
            try:
                d = int(input("Elbow diameter (in, 3–60): "))
                if 3 <= d <= 60:
                    break
                print("Diameter must be between 3 and 60 inches.")
            except ValueError:
                print("Please enter an integer value.")
        cfm = float(input("Airflow (CFM): "))
        return cls(d, cfm)

    def velocity_fpm(self):
        return round_velocity(self.cfm, self.diameter_in)

    def loss_coefficient(self):
        d = self.diameter_in
        table = self.C_TABLE
        keys = sorted(table)

        # Exact match
        if d in table:
            return table[d]

        # Find bounding diameters
        if d < keys[0]:
            d1, d2 = keys[0], keys[1]
        elif d > keys[-1]:
            d1, d2 = keys[-2], keys[-1]
        else:
            for i in range(len(keys) - 1):
                if keys[i] < d < keys[i + 1]:
                    d1, d2 = keys[i], keys[i + 1]
                    break

        # Linear interpolation
        c1, c2 = table[d1], table[d2]
        return c1 + (c2 - c1) * (d - d1) / (d2 - d1)

    # -------------------------
    # Geometry reporting
    # -------------------------

    def dimensions(self):
        return {
            "shape": "round",
            "diameter_in": self.diameter_in
        }


# ============================
# CD9-1 Butterfly Damper
# ============================
class ASHRAE_CD9_1_Butterfly_Damper(Fitting):

    C_OPEN = 0.60  # Fully open butterfly damper (ASHRAE CD9-1)

    def __init__(self, diameter_in, cfm):
        self.diameter_in = diameter_in
        self.cfm = cfm

    @classmethod
    def from_user_input(cls):

        # Get valid diameter
        while True:
            try:
                d = int(input("Duct diameter (in): "))
                if d <= 0:
                    print("Diameter must be positive.")
                    continue
                break
            except ValueError:
                print("Please enter an integer for diameter.")

        # Get valid airflow
        while True:
            try:
                cfm = float(input("Airflow (CFM): "))
                if cfm <= 0:
                    print("Airflow must be positive.")
                    continue
                break
            except ValueError:
                print("Please enter a number for airflow.")

        return cls(d, cfm)

    # -------------------------
    # Flow & Loss
    # -------------------------

    def velocity_fpm(self):
        return round_velocity(self.cfm, self.diameter_in)

    def loss_coefficient(self):
        return self.C_OPEN

    # -------------------------
    # Geometry reporting
    # -------------------------

    def dimensions(self):
        return {
            "shape": "round",
            "diameter_in": self.diameter_in,
            "cfm": self.cfm,
        }

# ============================
# CR3-1 Smooth Radius Elbow, Rectangular, No Vanes
# ============================
class ASHRAE_CR3_1_SmoothRadiusElbow(Fitting):
    # Cp values indexed as Cp[r/W][H/W]
    CP_TABLE = {
        0.50: {0.25: 1.53, 0.50: 1.38, 0.75: 1.29, 1.00: 1.18, 1.50: 1.06,
               2.00: 1.00, 3.00: 1.00, 4.00: 1.06, 5.00: 1.12, 6.00: 1.16, 8.00: 1.18},
        0.75: {0.25: 0.57, 0.50: 0.52, 0.75: 0.48, 1.00: 0.44, 1.50: 0.40,
               2.00: 0.39, 3.00: 0.39, 4.00: 0.40, 5.00: 0.42, 6.00: 0.43, 8.00: 0.44},
        1.00: {0.25: 0.27, 0.50: 0.25, 0.75: 0.23, 1.00: 0.21, 1.50: 0.19,
               2.00: 0.18, 3.00: 0.18, 4.00: 0.19, 5.00: 0.20, 6.00: 0.21, 8.00: 0.21},
        1.50: {0.25: 0.22, 0.50: 0.20, 0.75: 0.19, 1.00: 0.17, 1.50: 0.15,
               2.00: 0.14, 3.00: 0.14, 4.00: 0.15, 5.00: 0.16, 6.00: 0.17, 8.00: 0.17},
        2.00: {0.25: 0.20, 0.50: 0.18, 0.75: 0.16, 1.00: 0.15, 1.50: 0.14,
               2.00: 0.13, 3.00: 0.13, 4.00: 0.14, 5.00: 0.14, 6.00: 0.15, 8.00: 0.15},
    }

    # Angle factor K
    K_TABLE = {
        0: 0.00, 20: 0.31, 30: 0.45, 45: 0.60, 60: 0.78,
        75: 0.90, 90: 1.00, 110: 1.13, 130: 1.20, 150: 1.28, 180: 1.40
    }

    def __init__(self, width_in, height_in, r_w, theta_deg, cfm):
        self.width_in = width_in
        self.height_in = height_in
        self.r_w = r_w
        self.theta_deg = theta_deg
        self.cfm = cfm

    @classmethod
    def from_user_input(cls):
        # Get integer width
        while True:
            try:
                W = int(input("Duct width W (in): "))
                if W <= 0:
                    print("Width must be positive.")
                    continue
                break
            except ValueError:
                print("Please enter an integer for width.")

        # Get integer height
        while True:
            try:
                H = int(input("Duct height H (in): "))
                if H <= 0:
                    print("Height must be positive.")
                    continue
                break
            except ValueError:
                print("Please enter an integer for height.")

        # Get positive airflow
        while True:
            try:
                cfm = float(input("Airflow (CFM): "))
                if cfm <= 0:
                    print("Airflow must be positive.")
                    continue
                break
            except ValueError:
                print("Please enter a number for airflow.")

        # Select r/W
        r_w_options = sorted(cls.CP_TABLE)
        print("Available r/W values:", ", ".join(map(str, r_w_options)))
        while True:
            try:
                r_w = float(input("Select r/W: "))
                if r_w in cls.CP_TABLE:
                    break
                print(f"Invalid r/W. Choose from: {r_w_options}")
            except ValueError:
                print("Please enter a number for r/W.")

        # Select elbow angle
        theta_options = sorted(cls.K_TABLE)
        print("Available angles (deg):", ", ".join(map(str, theta_options)))
        while True:
            try:
                theta = int(input("Select elbow angle θ (deg): "))
                if theta in cls.K_TABLE:
                    break
                print(f"Invalid angle. Choose from: {theta_options}")
            except ValueError:
                print("Please enter an integer for angle.")

        return cls(W, H, r_w, theta, cfm)

    # -------------------------
    # Geometry & Flow Methods
    # -------------------------

    def actual_area_ft2(self):
        W_ft = self.width_in / 12
        H_ft = self.height_in / 12
        return W_ft * H_ft

    def velocity_fpm(self):
        return self.cfm / self.actual_area_ft2()

    def velocity_pressure_inwc(self):
        V = self.velocity_fpm()
        return (V / 4005) ** 2

    # -------------------------
    # Loss Coefficient & Loss
    # -------------------------

    def loss_coefficient(self):
        h_w_actual = self.height_in / self.width_in
        Cp_row = self.CP_TABLE[self.r_w]

        hw_values = sorted(Cp_row)
        h_w_used = hw_values[0]
        for hw in hw_values:
            if hw <= h_w_actual:
                h_w_used = hw
            else:
                break

        Cp = Cp_row[h_w_used]
        K = self.K_TABLE[self.theta_deg]
        return K * Cp

    # -------------------------
    # Geometry reporting
    # -------------------------

    def dimensions(self):
        return {
            "shape": "rectangular",
            "width_in": self.width_in,
            "height_in": self.height_in,
            "r_w": self.r_w,
            "theta_deg": self.theta_deg
        }

    # -------------------------
    # Results for main.py
    # -------------------------

    def results(self):
        """Return dictionary compatible with main.py summary."""
        velocity = self.velocity_fpm()
        vp = self.velocity_pressure_inwc()
        C = self.loss_coefficient()
        loss = C * vp  # inWC

        return {
            "W": self.width_in,
            "H": self.height_in,
            "velocity": velocity,
            "vp": vp,
            "C": C,
            "loss": loss
        }


# ============================
# CR3-6 Mitered Elbow No Vanes, Rectangular
# ============================
class ASHRAE_CR3_6_MiteredElbow(Fitting):
    C_TABLE = {
        20: {0.25: 0.08, 0.50: 0.08, 0.75: 0.08, 1.00: 0.07, 1.50: 0.07, 2.0: 0.07, 3.0: 0.06, 4.0: 0.06, 5.0: 0.05, 6.0: 0.05, 8.0: 0.05},
        30: {0.25: 0.18, 0.50: 0.17, 0.75: 0.17, 1.00: 0.16, 1.50: 0.15, 2.0: 0.15, 3.0: 0.13, 4.0: 0.13, 5.0: 0.12, 6.0: 0.12, 8.0: 0.11},
        45: {0.25: 0.38, 0.50: 0.37, 0.75: 0.36, 1.00: 0.34, 1.50: 0.33, 2.0: 0.31, 3.0: 0.28, 4.0: 0.27, 5.0: 0.26, 6.0: 0.25, 8.0: 0.24},
        60: {0.25: 0.60, 0.50: 0.59, 0.75: 0.57, 1.00: 0.55, 1.50: 0.52, 2.0: 0.49, 3.0: 0.46, 4.0: 0.43, 5.0: 0.41, 6.0: 0.39, 8.0: 0.38},
        75: {0.25: 0.89, 0.50: 0.87, 0.75: 0.84, 1.00: 0.81, 1.50: 0.77, 2.0: 0.73, 3.0: 0.67, 4.0: 0.63, 5.0: 0.61, 6.0: 0.58, 8.0: 0.57},
        90: {0.25: 1.30, 0.50: 1.27, 0.75: 1.23, 1.00: 1.18, 1.50: 1.13, 2.0: 1.07, 3.0: 0.98, 4.0: 0.92, 5.0: 0.89, 6.0: 0.85, 8.0: 0.83},
    }

    ALLOWED_ANGLES = [20, 30, 45, 60, 75, 90]

    def __init__(self, width_in, height_in, theta_deg, cfm):
        self.width_in = width_in
        self.height_in = height_in
        self.theta_deg = theta_deg
        self.cfm = cfm

    @classmethod
    def from_user_input(cls):
        # Width
        while True:
            try:
                W = int(input("Duct width W (in): "))
                if W <= 0:
                    print("Width must be positive.")
                    continue
                break
            except ValueError:
                print("Enter an integer value.")

        # Height
        while True:
            try:
                H = int(input("Duct height H (in): "))
                if H <= 0:
                    print("Height must be positive.")
                    continue
                break
            except ValueError:
                print("Enter an integer value.")

        # Angle
        print(f"Allowed elbow angles (degrees): {', '.join(map(str, cls.ALLOWED_ANGLES))}")
        while True:
            try:
                theta = int(input("Elbow angle θ (deg): "))
                if theta in cls.ALLOWED_ANGLES:
                    break
                print(f"Invalid angle. Choose from {cls.ALLOWED_ANGLES}")
            except ValueError:
                print("Enter an integer value.")

        # Airflow
        while True:
            try:
                cfm = float(input("Airflow (CFM): "))
                if cfm <= 0:
                    print("Airflow must be positive.")
                    continue
                break
            except ValueError:
                print("Enter a numeric value.")

        return cls(W, H, theta, cfm)

    # -------------------------
    # Geometry & Flow Methods
    # -------------------------

    def actual_area_ft2(self):
        return (self.width_in / 12) * (self.height_in / 12)

    def velocity_fpm(self):
        return self.cfm / self.actual_area_ft2()

    # -------------------------
    # Loss Coefficient & Loss
    # -------------------------

    def loss_coefficient(self):
        aspect = self.height_in / self.width_in

        C_row = self.C_TABLE[self.theta_deg]
        ratios = sorted(C_row)

        # Floor aspect ratio to nearest table value
        r_used = ratios[0]
        for r in ratios:
            if r <= aspect:
                r_used = r
            else:
                break

        # Warn if clipping occurred
        if aspect < ratios[0]:
            print(
                f"Warning: H/W = {aspect:.3f} below table minimum "
                f"({ratios[0]}). Using {ratios[0]}."
            )
        elif aspect > ratios[-1]:
            print(
                f"Warning: H/W = {aspect:.3f} above table maximum "
                f"({ratios[-1]}). Using {ratios[-1]}."
            )

        return C_row[r_used]

    # -------------------------
    # Reporting
    # -------------------------

    def dimensions(self):
        return {
            "shape": "rectangular",
            "width_in": self.width_in,
            "height_in": self.height_in,
            "theta_deg": self.theta_deg,
        }

    def results(self):
        velocity = self.velocity_fpm()
        vp = (velocity / 4005) ** 2
        C = self.loss_coefficient()
        loss = C * vp

        return {
            "W": float(self.width_in),
            "H": float(self.height_in),
            "L": 0.0,  # safe default for main.py
            "velocity": velocity,
            "vp": vp,
            "C": C,
            "loss": loss,
        }


# ============================
# CR3-12 Mitered Elbow Single Vanes, Rectangular
# ============================
class ASHRAE_CR3_12_MiteredElbow(Fitting):
    def __init__(self, width_in, height_in, cfm):
        self.width_in = width_in
        self.height_in = height_in
        self.cfm = cfm
        self.C = 0.33  # fixed loss coefficient

    @classmethod
    def from_user_input(cls):
        # Width
        while True:
            try:
                width = int(input("Duct width (in): "))
                if width <= 0:
                    print("Width must be a positive integer.")
                    continue
                break
            except ValueError:
                print("Please enter an integer value.")

        # Height
        while True:
            try:
                height = int(input("Duct height (in): "))
                if height <= 0:
                    print("Height must be a positive integer.")
                    continue
                break
            except ValueError:
                print("Please enter an integer value.")

        # Airflow
        while True:
            try:
                cfm = float(input("Airflow (CFM): "))
                if cfm <= 0:
                    print("Airflow must be positive.")
                    continue
                break
            except ValueError:
                print("Please enter a numeric value.")

        return cls(width, height, cfm)

    def velocity_fpm(self):
        area_ft2 = (self.width_in * self.height_in) / 144  # in² → ft²
        return self.cfm / area_ft2

    def dimensions(self):
        return {
            "shape": "rectangular",
            "width_in": self.width_in,
            "height_in": self.height_in,
            "cfm": self.cfm
        }

    def loss_coefficient(self):
        return self.C

    def results(self):
        velocity = self.velocity_fpm()
        vp = (velocity / 4005) ** 2
        loss = self.C * vp
        return {
            "velocity": velocity,
            "vp": vp,
            "C": self.C,
            "loss": loss
        }


# ============================
# ER5-2 Tee, Round Branch to Rectangular Main (Converging)
# ============================
class ASHRAE_ER5_2_Tee(Fitting):
    # Loss coefficient tables
    CB_TABLE = {  # branch loss coeff by Qb/Qc ratio
        0.1: -14.00, 0.2: -2.38, 0.3: 0.50, 0.4: 0.65, 0.5: 1.03,
        0.6: 1.17, 0.7: 1.19, 0.8: 1.33, 0.9: 1.51, 1.0: 1.44
    }
    CS_TABLE = {  # straight/main loss coeff by Qs/Qc ratio
        0.1: 22.15, 0.2: 11.91, 0.3: 6.54, 0.4: 3.74, 0.5: 2.23,
        0.6: 1.33, 0.7: 0.76, 0.8: 0.38, 0.9: 0.10, 1.0: 0.00
    }

    def __init__(self, main_width_in, main_height_in, main_cfm,
                 branch_diam_in, branch_cfm, flow_type="main"):
        self.main_width_in = main_width_in
        self.main_height_in = main_height_in
        self.main_cfm = main_cfm
        self.branch_diam_in = branch_diam_in
        self.branch_cfm = branch_cfm
        self.flow_type = flow_type  # 'main' or 'branch'

    @classmethod
    def from_user_input(cls):
        print("Enter MAIN duct dimensions and CFM (Rectangular):")

        # Main width
        while True:
            try:
                main_w = int(input("Main duct width (in): "))
                if main_w <= 0:
                    print("Width must be a positive integer.")
                    continue
                break
            except ValueError:
                print("Please enter an integer value.")

        # Main height
        while True:
            try:
                main_h = int(input("Main duct height (in): "))
                if main_h <= 0:
                    print("Height must be a positive integer.")
                    continue
                break
            except ValueError:
                print("Please enter an integer value.")

        # Main airflow
        while True:
            try:
                main_cfm = float(input("Main duct CFM (Qs): "))
                if main_cfm <= 0:
                    print("CFM must be positive.")
                    continue
                break
            except ValueError:
                print("Please enter a numeric value.")

        print("\nEnter BRANCH duct diameter and CFM (Round):")

        # Branch diameter
        while True:
            try:
                branch_d = int(input("Branch duct diameter (in): "))
                if branch_d <= 0:
                    print("Diameter must be a positive integer.")
                    continue
                break
            except ValueError:
                print("Please enter an integer value.")

        # Branch airflow
        while True:
            try:
                branch_cfm = float(input("Branch duct CFM (Qb): "))
                if branch_cfm <= 0:
                    print("CFM must be positive.")
                    continue
                break
            except ValueError:
                print("Please enter a numeric value.")

        # Flow path selection
        while True:
            flow_choice = input(
                "Analyze loss for 'main' straight flow or 'branch' flow? (main/branch): "
            ).strip().lower()
            if flow_choice in ("main", "branch"):
                break
            print("Invalid input. Please enter 'main' or 'branch'.")

        return cls(main_w, main_h, main_cfm, branch_d, branch_cfm, flow_choice)

    # -------------------------
    # Velocity
    # -------------------------

    def velocity_fpm(self):
        main_area = (self.main_width_in * self.main_height_in) / 144  # ft²
        branch_area = (pi * (self.branch_diam_in / 2) ** 2) / 144     # ft²

        return {
            "main": self.main_cfm / main_area,
            "branch": self.branch_cfm / branch_area
        }

    # -------------------------
    # Geometry reporting
    # -------------------------

    def dimensions(self):
        return {
            "main": {
                "shape": "rectangular",
                "width_in": self.main_width_in,
                "height_in": self.main_height_in,
                "cfm": self.main_cfm
            },
            "branch": {
                "shape": "round",
                "diameter_in": self.branch_diam_in,
                "cfm": self.branch_cfm
            }
        }

    # -------------------------
    # Loss coefficient
    # -------------------------

    def _interp_coeff(self, table, ratio):
        keys = sorted(table)
        if ratio <= keys[0]:
            return table[keys[0]]
        if ratio >= keys[-1]:
            return table[keys[-1]]
        for i in range(len(keys) - 1):
            if keys[i] <= ratio <= keys[i + 1]:
                x0, x1 = keys[i], keys[i + 1]
                y0, y1 = table[x0], table[x1]
                return y0 + (y1 - y0) * (ratio - x0) / (x1 - x0)
        return table[keys[0]]

    def loss_coefficient(self):
        Qc = self.main_cfm + self.branch_cfm

        if self.flow_type == "main":
            ratio = self.main_cfm / Qc
            return self._interp_coeff(self.CS_TABLE, ratio)
        else:
            ratio = self.branch_cfm / Qc
            return self._interp_coeff(self.CB_TABLE, ratio)

    # -------------------------
    # Results
    # -------------------------

    def results(self):
        velocities = self.velocity_fpm()

        if self.flow_type == "main":
            V = velocities["main"]
            flow_label = "Main (Straight-Through Flow)"
        else:
            V = velocities["branch"]
            flow_label = "Branch (Turning Flow)"

        vp = (V / 4005) ** 2
        C = self.loss_coefficient()
        loss = C * vp

        return {
            "flow_path": flow_label,
            "velocity": V,
            "vp": vp,
            "C": C,
            "loss": loss
        }


# ============================
# ER5-3 Tee, Rectangular Branch to Rectangular Main (Converging)
# ============================
class ASHRAE_ER5_3_Tee(Fitting):
    # Loss coefficient tables
    CB_TABLE = {
        0.1: -19.38, 0.2: -3.75, 0.3: -0.74, 0.4: 0.48, 0.5: 0.66,
        0.6: 0.75, 0.7: 0.85, 0.8: 0.77, 0.9: 0.83, 1.0: 0.83
    }
    CS_TABLE = {
        0.1: 22.15, 0.2: 11.91, 0.3: 6.54, 0.4: 3.74, 0.5: 2.23,
        0.6: 1.33, 0.7: 0.76, 0.8: 0.38, 0.9: 0.10, 1.0: 0.00
    }

    def __init__(self, main_width_in, main_height_in, main_cfm,
                 branch_width_in, branch_height_in, branch_cfm, flow_type="main"):
        self.main_width_in = main_width_in
        self.main_height_in = main_height_in
        self.main_cfm = main_cfm
        self.branch_width_in = branch_width_in
        self.branch_height_in = branch_height_in
        self.branch_cfm = branch_cfm
        self.flow_type = flow_type

    @classmethod
    def from_user_input(cls):
        def positive_int(prompt):
            while True:
                try:
                    val = int(input(prompt))
                    if val <= 0:
                        print("Value must be a positive integer.")
                        continue
                    return val
                except ValueError:
                    print("Please enter an integer value.")

        def positive_float(prompt):
            while True:
                try:
                    val = float(input(prompt))
                    if val <= 0:
                        print("Value must be positive.")
                        continue
                    return val
                except ValueError:
                    print("Please enter a numeric value.")

        print("Enter MAIN duct dimensions and CFM (Rectangular):")
        main_w = positive_int("Main duct width (in): ")
        main_h = positive_int("Main duct height (in): ")
        main_cfm = positive_float("Main duct CFM (Qs): ")

        print("\nEnter BRANCH duct dimensions and CFM (Rectangular):")
        branch_w = positive_int("Branch duct width (in): ")
        branch_h = positive_int("Branch duct height (in): ")
        branch_cfm = positive_float("Branch duct CFM (Qb): ")

        while True:
            flow_choice = input(
                "Analyze loss for 'main' straight flow or 'branch' flow? (main/branch): "
            ).strip().lower()
            if flow_choice in ("main", "branch"):
                break
            print("Invalid input. Please enter 'main' or 'branch'.")

        return cls(
            main_w, main_h, main_cfm,
            branch_w, branch_h, branch_cfm,
            flow_choice
        )

    def velocity_fpm(self):
        main_area = (self.main_width_in * self.main_height_in) / 144
        branch_area = (self.branch_width_in * self.branch_height_in) / 144
        return {
            "main": self.main_cfm / main_area,
            "branch": self.branch_cfm / branch_area
        }

    def dimensions(self):
        return {
            "main": {
                "shape": "rectangular",
                "width_in": self.main_width_in,
                "height_in": self.main_height_in,
                "cfm": self.main_cfm
            },
            "branch": {
                "shape": "rectangular",
                "width_in": self.branch_width_in,
                "height_in": self.branch_height_in,
                "cfm": self.branch_cfm
            }
        }

    def _interp_coeff(self, table, ratio):
        keys = sorted(table)
        if ratio <= keys[0]:
            return table[keys[0]]
        if ratio >= keys[-1]:
            return table[keys[-1]]
        for i in range(len(keys) - 1):
            if keys[i] <= ratio <= keys[i + 1]:
                x0, x1 = keys[i], keys[i + 1]
                y0, y1 = table[x0], table[x1]
                return y0 + (y1 - y0) * (ratio - x0) / (x1 - x0)
        return table[keys[0]]

    def loss_coefficient(self):
        Qc = self.main_cfm + self.branch_cfm
        if self.flow_type == "main":
            ratio = self.main_cfm / Qc if Qc else 0
            return self._interp_coeff(self.CS_TABLE, ratio)
        else:
            ratio = self.branch_cfm / Qc if Qc else 0
            return self._interp_coeff(self.CB_TABLE, ratio)

    def results(self):
        velocities = self.velocity_fpm()
        if self.flow_type == "main":
            V = velocities["main"]
            flow_label = "Main (Straight-Through Flow)"
        else:
            V = velocities["branch"]
            flow_label = "Branch (Turning Flow)"

        vp = (V / 4005) ** 2
        C = self.loss_coefficient()
        loss = C * vp

        return {
            "flow_path": flow_label,
            "velocity": V,
            "vp": vp,
            "C": C,
            "loss": loss
        }


# ============================
# SMACNA Smooth Radius Elbow (Die Stamped)
# ============================
class SMACNA_SmoothRadiusElbow(Fitting):
    """
    Elbow, Smooth Radius (Die Stamped), Round
    """

    # Base loss coefficients for 90° elbows
    C_90_TABLE = {
        0.5: 0.71,
        0.75: 0.33,
        1.0: 0.22,
        1.5: 0.15,
        2.0: 0.13,
        2.5: 0.12,
    }

    # Angle correction factors (K)
    ANGLE_FACTOR_TABLE = {
        0: 0.00,
        20: 0.31,
        30: 0.45,
        45: 0.60,
        60: 0.78,
        75: 0.90,
        90: 1.00,
        110: 1.13,
        130: 1.20,
        150: 1.28,
        180: 1.40,
    }

    def __init__(self, diameter_in, r_d, theta_deg, cfm):
        self.diameter_in = diameter_in
        self.r_d = r_d
        self.theta_deg = theta_deg
        self.cfm = cfm

    @classmethod
    def from_user_input(cls):
        valid_r_d = sorted(cls.C_90_TABLE)
        valid_angles = sorted(cls.ANGLE_FACTOR_TABLE)

        # Validate diameter as positive integer
        while True:
            try:
                d = int(input("Duct diameter (in): "))
                if d > 0:
                    break
                print("Duct diameter must be a positive integer.")
            except ValueError:
                print("Please enter an integer value.")

        print("Available r/D ratios:", ", ".join(map(str, valid_r_d)))
        while True:
            try:
                r_d = float(input("r/D ratio: "))
                if r_d in cls.C_90_TABLE:
                    break
                print("Invalid r/D ratio. Choose from the list above.")
            except ValueError:
                print("Please enter a numeric value.")

        print("Available elbow angles (degrees):", ", ".join(map(str, valid_angles)))
        while True:
            try:
                theta = int(input("Elbow angle (deg): "))
                if theta in cls.ANGLE_FACTOR_TABLE:
                    break
                print("Invalid angle. Choose from the list above.")
            except ValueError:
                print("Please enter an integer value.")

        # Airflow as positive float
        while True:
            try:
                cfm = float(input("Airflow (CFM): "))
                if cfm > 0:
                    break
                print("Airflow must be positive.")
            except ValueError:
                print("Please enter a numeric value.")

        return cls(d, r_d, theta, cfm)

    def velocity_fpm(self):
        return round_velocity(self.cfm, self.diameter_in)

    def loss_coefficient(self):
        c_90 = self.C_90_TABLE[self.r_d]
        k_theta = self.ANGLE_FACTOR_TABLE[self.theta_deg]
        return c_90 * k_theta

    def dimensions(self):
        return {
            "shape": "round",
            "diameter_in": self.diameter_in,
            "r_d": self.r_d,
            "theta_deg": self.theta_deg,
            "cfm": self.cfm,
        }

# ============================
# SMACNA Rectangular Z-Shaped Elbow
# ============================
class SMACNA_Rectangular_Z_Elbow(Fitting):
    """
    90° Rectangular Z-Shaped Elbow (No Vanes)
    """

    # Base C values for L/H ratio
    LH_TABLE = {
        0.0: 0.0, 0.4: 0.62, 0.6: 0.90, 0.8: 1.6, 1.0: 2.6,
        1.2: 3.6, 1.4: 4.0, 1.6: 4.2, 1.8: 4.2, 2.0: 4.2,
        2.4: 3.7, 2.8: 3.3, 3.2: 3.2, 4.0: 3.1, 5.0: 2.9,
        6.0: 2.8, 7.0: 2.7, 9.0: 2.6, 10.0: 2.5,
    }

    # W/H correction factors
    WH_TABLE = {
        0.25: 1.10, 0.50: 1.07, 0.75: 1.04, 1.00: 1.00, 1.50: 0.95,
        2.00: 0.90, 3.00: 0.83, 4.00: 0.78, 6.00: 0.72, 8.00: 0.70,
    }

    # Reynolds number correction (Re / 10^4)
    RE_TABLE = {
        1: 1.40, 2: 1.26, 3: 1.19, 4: 1.14, 6: 1.09,
        8: 1.06, 10: 1.04, 14: 1.00,
    }

    def __init__(self, width_in, height_in, length_in, cfm, theta_deg=90):
        self.width_in = width_in
        self.height_in = height_in
        self.length_in = length_in
        self.cfm = cfm
        self.theta_deg = theta_deg  # Optional for other elbows

    @staticmethod
    def _interpolate(x, table):
        keys = sorted(table)
        if x <= keys[0]:
            return table[keys[0]]
        if x >= keys[-1]:
            return table[keys[-1]]
        for x1, x2 in zip(keys[:-1], keys[1:]):
            if x1 <= x <= x2:
                y1, y2 = table[x1], table[x2]
                return y1 + (y2 - y1) * (x - x1) / (x2 - x1)

    @classmethod
    def from_user_input(cls):
        while True:
            try:
                width_in = int(input("Enter duct width W (in): "))
                if width_in <= 0:
                    print("Width must be a positive integer.")
                    continue
                break
            except ValueError:
                print("Please enter a valid integer.")

        while True:
            try:
                height_in = int(input("Enter duct height H (in): "))
                if height_in <= 0:
                    print("Height must be a positive integer.")
                    continue
                break
            except ValueError:
                print("Please enter a valid integer.")

        while True:
            try:
                length_in = int(input("Enter offset length L (in): "))
                if length_in <= 0:
                    print("Length must be integer greater than zero.")
                    continue
                break
            except ValueError:
                print("Please enter a valid integer.")

        while True:
            try:
                cfm = int(input("Enter airflow (CFM): "))
                if cfm <= 0:
                    print("Airflow must be a positive integer.")
                    continue
                break
            except ValueError:
                print("Please enter a valid integer.")

        return cls(width_in, height_in, length_in, cfm)

    def area_sqft(self):
        return (self.width_in * self.height_in) / 144.0

    def velocity_fpm(self):
        return self.cfm / self.area_sqft()

    def hydraulic_diameter(self):
        return (2 * self.width_in * self.height_in) / (self.width_in + self.height_in)

    def reynolds_number(self):
        V = self.velocity_fpm()
        D = self.hydraulic_diameter()
        return 8.56 * D * V

    def loss_coefficient(self):
        LH = self.length_in / self.height_in
        WH = self.width_in / self.height_in

        # Base C from L/H
        if LH > max(self.LH_TABLE):
            C_base = self._interpolate(max(self.LH_TABLE), self.LH_TABLE)
        else:
            C_base = self._interpolate(LH, self.LH_TABLE)

        # W/H correction
        K_wh = self._interpolate(WH, self.WH_TABLE)

        # Reynolds correction
        Re_scaled = self.reynolds_number() / 1e4
        K_re = self._interpolate(Re_scaled, self.RE_TABLE)

        return C_base * K_wh * K_re

    def pressure_loss(self):
        V = self.velocity_fpm()
        vp = (V / 4005) ** 2
        return self.loss_coefficient() * vp

    def results(self):
        # Sanity checks
        if self.width_in <= 0 or self.height_in <= 0 or self.length_in < 0:
            raise ValueError("Width and height must be > 0, length must be >= 0")
        if self.area_sqft() <= 0:
            raise ValueError("Calculated duct area is zero or negative")

        velocity = self.velocity_fpm()
        vp = (velocity / 4005) ** 2
        C = self.loss_coefficient()
        loss = C * vp

        return {
            "velocity": velocity,
            "vp": vp,
            "C": C,
            "loss": loss,
            "W": self.width_in,
            "H": self.height_in,
            "L": self.length_in,
            "theta_deg": self.theta_deg,   # will show 90° for Z-Elbow
            "L_over_H": self.length_in / self.height_in,
            "W_over_H": self.width_in / self.height_in,
            "hydraulic_diameter": self.hydraulic_diameter(),
            "reynolds": self.reynolds_number(),
        }


# ============================
# SMACNA Converging Tee, 90° Round
# ============================
class SMACNA_Converging_Tee_Round:
    # Table columns (area ratio Ab/Ac)
    AREA_RATIO_COLS = [0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0]

    # Table rows (flow ratio Qb/Qc)
    FLOW_RATIO_ROWS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    # ------------------------
    # Branch loss coefficient table
    # ------------------------
    CB_TABLE = {
        0.1: {0.1: 0.4,  0.2: -0.37, 0.3: -0.51, 0.4: -0.46, 0.6: -0.50, 0.8: -0.51, 1.0: -0.52},
        0.2: {0.1: 3.8,  0.2: 0.72, 0.3: 0.17, 0.4: -0.02, 0.6: -0.14, 0.8: -0.18, 1.0: -0.24},
        0.3: {0.1: 9.2,  0.2: 2.3, 0.3: 1.0, 0.4: 0.44, 0.6: 0.21, 0.8: 0.11, 1.0: -0.08},
        0.4: {0.1: 16.0, 0.2: 4.3, 0.3: 2.1, 0.4: 0.94, 0.6: 0.54, 0.8: 0.40, 1.0: 0.32},
        0.5: {0.1: 26,  0.2: 6.8, 0.3: 3.2, 0.4: 1.1, 0.6: 0.66, 0.8: 0.49, 1.0: 0.42},
        0.6: {0.1: 37,  0.2: 9.7, 0.3: 4.7, 0.4: 1.6, 0.6: 0.92, 0.8: 0.69, 1.0: 0.57},
        0.7: {0.1: 43,  0.2: 13, 0.3: 6.3, 0.4: 2.1, 0.6: 1.2, 0.8: 0.88, 1.0: 0.72},
        0.8: {0.1: 65,  0.2: 17, 0.3: 7.9, 0.4: 2.7, 0.6: 1.5, 0.8: 1.1, 1.0: 0.86},
        0.9: {0.1: 82,  0.2: 21, 0.3: 9.7, 0.4: 3.4, 0.6: 1.8, 0.8: 1.2, 1.0: 0.99},
        1.0: {0.1: 101, 0.2: 26, 0.3: 12,  0.4: 4.0, 0.6: 2.1, 0.8: 1.4, 1.0: 1.1},
    }

    # ------------------------
    # Main (straight-through) loss coefficient table
    # ------------------------
    CS_TABLE = {
        0.1: 0.16,
        0.2: 0.27,
        0.3: 0.38,
        0.4: 0.46,
        0.5: 0.53,
        0.6: 0.57,
        0.7: 0.59,
        0.8: 0.60,
        0.9: 0.59,
        1.0: 0.55,
    }

    def __init__(self, main_diam_in, branch_diam_in, Qs, Qb, flow_type):
        self.main_diam_in = main_diam_in
        self.branch_diam_in = branch_diam_in
        self.Qs = Qs
        self.Qb = Qb
        self.flow_type = flow_type  # "main" or "branch"

    # ------------------------
    # User input
    # ------------------------
    @classmethod
    def from_user_input(cls):
        while True:
            try:
                main_d = int(input("Main duct diameter (in): "))
                if main_d <= 0:
                    raise ValueError
                break
            except ValueError:
                print("Main diameter must be a positive integer.")

        while True:
            try:
                Qs = float(input("Main duct airflow Qs (CFM): "))
                if Qs <= 0:
                    raise ValueError
                break
            except ValueError:
                print("Invalid main airflow.")

        while True:
            try:
                branch_d = int(input("Branch duct diameter (in): "))
                if branch_d <= 0 or branch_d > main_d:
                    raise ValueError
                break
            except ValueError:
                print("Branch diameter must be a positive integer and ≤ main diameter.")

        while True:
            try:
                Qb = float(input("Branch duct airflow Qb (CFM): "))
                if Qb <= 0:
                    raise ValueError
                break
            except ValueError:
                print("Invalid branch airflow.")

        while True:
            flow_type = input("Calculate loss for 'main' or 'branch'? ").strip().lower()
            if flow_type in ("main", "branch"):
                break
            print("Enter 'main' or 'branch'.")

        return cls(main_d, branch_d, Qs, Qb, flow_type)

    # ------------------------
    # Geometry helpers
    # ------------------------
    def _area_sqft(self, d_in):
        return pi * (d_in / 12) ** 2 / 4

    def _round_down(self, value, table):
        return max(x for x in table if x <= value)

    def _round_up(self, value, table):
        return min(x for x in table if x >= value)

    # ------------------------
    # Results
    # ------------------------
    def results(self):
        Qc = self.Qs + self.Qb

        area_main = self._area_sqft(self.main_diam_in)
        area_branch = self._area_sqft(self.branch_diam_in)

        # SMACNA: downstream velocity for both paths
        Vc = Qc / area_main
        vp = (Vc / 4005) ** 2

        flow_ratio = self.Qb / Qc
        area_ratio = area_branch / area_main

        flow_used = self._round_up(flow_ratio, self.FLOW_RATIO_ROWS)
        area_used = self._round_down(area_ratio, self.AREA_RATIO_COLS)

        C_main = self.CS_TABLE[flow_used]
        C_branch = self.CB_TABLE[flow_used][area_used]

        if self.flow_type == "main":
            C_used = C_main
            loss = C_main * vp
            flow_path = "Main (Straight-Through Flow)"
        else:
            C_used = C_branch
            loss = C_branch * vp
            flow_path = "Branch"

        return {
            "flow_path": flow_path,
            "velocity": Vc,
            "vp": vp,
            "C": C_used,
            "loss": loss,
        }

    # ------------------------
    # Compatibility helpers
    # ------------------------
    @property
    def cfm(self):
        return self.Qs + self.Qb

    def dimensions(self):
        return {
            "main": {
                "shape": "round",
                "diameter_in": self.main_diam_in,
                "cfm": self.Qs,
            },
            "branch": {
                "shape": "round",
                "diameter_in": self.branch_diam_in,
                "cfm": self.Qb,
            },
        }


# ============================
# SMACNA Conical Tee, 90° Round out of Round Main
# ============================
class SMACNA_Conical_Tee_Round:
    # ------------------------
    # Branch loss: Vb / Vc
    # ------------------------
    VEL_RATIO_COLS_BRANCH = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]

    CB_TABLE = {
        0.0: 1.00,
        0.2: 0.85,
        0.4: 0.74,
        0.6: 0.62,
        0.8: 0.52,
        1.0: 0.42,
        1.2: 0.36,
        1.4: 0.32,
        1.6: 0.32,
        1.8: 0.37,
        2.0: 0.52,
    }

    # ------------------------
    # Main loss: Vs / Vc
    # ------------------------
    VEL_RATIO_COLS_MAIN = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0]

    CS_TABLE = {
        0.0: 0.35,
        0.1: 0.28,
        0.2: 0.22,
        0.3: 0.17,
        0.4: 0.13,
        0.5: 0.09,
        0.6: 0.06,
        0.8: 0.02,
        1.0: 0.00,
    }

    # ------------------------
    # Constructor
    # ------------------------
    def __init__(self, main_diam_in, branch_diam_in, Qc, Qb, flow_type):
        self.main_diam_in = main_diam_in
        self.branch_diam_in = branch_diam_in
        self.Qc = Qc                  # upstream flow
        self.Qb = Qb                  # branch flow
        self.Qs = Qc - Qb             # straight-through flow
        self.flow_type = flow_type    # "main" or "branch"

    # ------------------------
    # User input
    # ------------------------
    @classmethod
    def from_user_input(cls):
        while True:
            try:
                main_d = int(input("Main duct diameter (in): "))
                if main_d <= 0:
                    raise ValueError
                break
            except ValueError:
                print("Main diameter must be a positive integer.")

        while True:
            try:
                Qc = float(input("Upstream airflow Qc (CFM): "))
                if Qc <= 0:
                    raise ValueError
                break
            except ValueError:
                print("Invalid upstream airflow.")

        while True:
            try:
                branch_d = int(input("Branch duct diameter (in): "))
                if branch_d <= 0 or branch_d > main_d:
                    raise ValueError
                break
            except ValueError:
                print("Branch diameter must be a positive integer and ≤ main diameter.")

        while True:
            try:
                Qb = float(input("Branch airflow Qb (CFM): "))
                if Qb <= 0 or Qb >= Qc:
                    raise ValueError
                break
            except ValueError:
                print("Branch airflow must be positive and less than Qc.")

        while True:
            flow_type = input("Calculate loss for 'main' or 'branch'? ").strip().lower()
            if flow_type in ("main", "branch"):
                break
            print("Enter 'main' or 'branch'.")

        return cls(main_d, branch_d, Qc, Qb, flow_type)

    # ------------------------
    # Helpers
    # ------------------------
    def _area_sqft(self, d_in):
        return pi * (d_in / 12) ** 2 / 4

    def _round_down(self, value, table):
        """
        Returns the largest table value <= value.
        Conservative rounding: picks a lower velocity ratio, giving higher C.
        """
        if value <= table[0]:
            return table[0]
        return max(x for x in table if x <= value)

    # ------------------------
    # Results
    # ------------------------
    def results(self):
        area_main = self._area_sqft(self.main_diam_in)
        area_branch = self._area_sqft(self.branch_diam_in)

        # Velocities
        Vc = self.Qc / area_main        # Upstream velocity (where vp is calculated)
        Vs = self.Qs / area_main        # Straight-through downstream velocity
        Vb = self.Qb / area_branch      # Branch velocity

        # Upstream velocity pressure (always used for loss calc)
        vp_c = (Vc / 4005) ** 2

        # Velocity to report is always upstream velocity (Vc)
        velocity = Vc

        if self.flow_type == "branch":
            vel_ratio = Vb / Vc
            ratio_used = self._round_down(vel_ratio, self.VEL_RATIO_COLS_BRANCH)
            C_used = self.CB_TABLE[ratio_used]
            loss = C_used * vp_c
            flow_path = "Branch"
        else:
            vel_ratio = Vs / Vc
            ratio_used = self._round_down(vel_ratio, self.VEL_RATIO_COLS_MAIN)
            C_used = self.CS_TABLE[ratio_used]
            loss = C_used * vp_c
            flow_path = "Main (Straight-Through Flow)"

        return {
            "flow_path": flow_path,
            "velocity": velocity,  # upstream velocity
            "vp": vp_c,
            "C": C_used,
            "loss": loss,
        }

    # ------------------------
    # Compatibility helpers
    # ------------------------
    @property
    def cfm(self):
        return self.Qc

    def dimensions(self):
        return {
            "main": {
                "shape": "round",
                "diameter_in": self.main_diam_in,
                "cfm": self.Qs,
            },
            "branch": {
                "shape": "round",
                "diameter_in": self.branch_diam_in,
                "cfm": self.Qb,
            },
        }


# ============================
# SMACNA Rectangular Main to Conical Supply Branch
# ============================
class SMACNA_Rectangular_Main_Conical_Branch:
    # ------------------------
    # Branch loss: Vb / Vc
    # ------------------------
    VEL_RATIO_COLS_BRANCH = [0.4, 0.50, 0.75, 1.0, 1.3, 1.5]

    CB_TABLE = {
        0.4: 0.8,
        0.5: 0.83,
        0.75: 0.90,
        1.0: 1.0,
        1.3: 1.1,
        1.5: 1.4,
    }

    # ------------------------
    # Main loss: Vs / Vc
    # ------------------------
    VEL_RATIO_COLS_MAIN = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0]

    CS_TABLE = {
        0.0: 0.35,
        0.1: 0.28,
        0.2: 0.22,
        0.3: 0.17,
        0.4: 0.13,
        0.5: 0.09,
        0.6: 0.06,
        0.8: 0.02,
        1.0: 0.00,
    }

    # ------------------------
    # Constructor
    # ------------------------
    def __init__(self, main_width_in, main_height_in, branch_diam_in, Qc, Qb, flow_type):
        self.main_width_in = main_width_in
        self.main_height_in = main_height_in
        self.branch_diam_in = branch_diam_in
        self.Qc = Qc
        self.Qb = Qb
        self.Qs = Qc - Qb
        self.flow_type = flow_type

    # ------------------------
    # User input
    # ------------------------
    @classmethod
    def from_user_input(cls):
        while True:
            try:
                w = int(input("Main duct width (in): "))
                if w <= 0:
                    raise ValueError
                break
            except ValueError:
                print("Width must be a positive integer.")

        while True:
            try:
                h = int(input("Main duct height (in): "))
                if h <= 0:
                    raise ValueError
                break
            except ValueError:
                print("Height must be a positive integer.")

        while True:
            try:
                Qc = float(input("Upstream airflow Qc (CFM): "))
                if Qc <= 0:
                    raise ValueError
                break
            except ValueError:
                print("Invalid upstream airflow.")

        while True:
            try:
                branch_d = int(input("Branch duct diameter (in): "))
                if branch_d <= 0:
                    raise ValueError
                break
            except ValueError:
                print("Branch diameter must be a positive integer.")

        while True:
            try:
                Qb = float(input("Branch airflow Qb (CFM): "))
                if Qb <= 0 or Qb >= Qc:
                    raise ValueError
                break
            except ValueError:
                print("Branch airflow must be positive and less than Qc.")

        while True:
            flow_type = input("Calculate loss for 'main' or 'branch'? ").strip().lower()
            if flow_type in ("main", "branch"):
                break
            print("Enter 'main' or 'branch'.")

        return cls(w, h, branch_d, Qc, Qb, flow_type)

    # ------------------------
    # Helpers
    # ------------------------
    def _area_rect_sqft(self, w_in, h_in):
        """Area of rectangular duct in ft²."""
        return (w_in * h_in) / 144  # in² → ft²

    def _area_round_sqft(self, d_in):
        """Area of round duct in ft²."""
        return pi * (d_in / 12) ** 2 / 4

    def _round_down(self, value, table):
        """Conservative rounding: largest table value ≤ value."""
        if value <= table[0]:
            return table[0]
        return max(x for x in table if x <= value)

    # ------------------------
    # Results
    # ------------------------
    def results(self):
        area_main = self._area_rect_sqft(self.main_width_in, self.main_height_in)
        area_branch = self._area_round_sqft(self.branch_diam_in)

        # Velocities
        Vc = self.Qc / area_main  # upstream (rectangular main) velocity
        Vs = self.Qs / area_main  # straight-through downstream
        Vb = self.Qb / area_branch  # branch velocity

        # Upstream velocity pressure
        vp_c = (Vc / 4005) ** 2

        velocity = Vc  # always report upstream velocity

        if self.flow_type == "branch":
            vel_ratio = Vb / Vc
            ratio_used = self._round_down(vel_ratio, self.VEL_RATIO_COLS_BRANCH)
            C_used = self.CB_TABLE[ratio_used]
            loss = C_used * vp_c
            flow_path = "Branch"
        else:
            vel_ratio = Vs / Vc
            ratio_used = self._round_down(vel_ratio, self.VEL_RATIO_COLS_MAIN)
            C_used = self.CS_TABLE[ratio_used]
            loss = C_used * vp_c
            flow_path = "Main (Straight-Through Flow)"

        return {
            "flow_path": flow_path,
            "velocity": velocity,
            "vp": vp_c,
            "C": C_used,
            "loss": loss,
        }

    # ------------------------
    # Compatibility helpers
    # ------------------------
    @property
    def cfm(self):
        return self.Qc

    def dimensions(self):
        return {
            "main": {
                "shape": "rectangular",
                "width_in": self.main_width_in,
                "height_in": self.main_height_in,
                "cfm": self.Qs,
            },
            "branch": {
                "shape": "round",
                "diameter_in": self.branch_diam_in,
                "cfm": self.Qb,
            },
        }


