import numpy as np
from scipy.optimize import fsolve

GRAVITY = 32.174 # ft/s^2
SHEET_METAL_EPSILON = 0.0007  # 0.0005 is typical of sheet metal. 0.0007 seems to match McQuay's sizer (more conservative).
AIR_DYN_VISC = 0.0432  # lbm/(ft·h) at 68°F and sea level.
AIR_DENSITY = 0.075  # lbm/ft³ at 68°F and sea level.

def reynolds_num(velocity, diam):
    """Simple function to calculate Reynolds number of the air
    velocity in fpm
    diam in inches"""
    reynolds = (AIR_DENSITY * velocity * diam/12) / (AIR_DYN_VISC/60)
    return reynolds

def darcy_weisbach_pressure_loss(re, velocity, diam, duct_length, initial_guess=0.02):
    """
    Calculates pressure loss in inWC per 100 ft of straight duct
    using the Colebrook-White equation.

    Parameters:
    re       : Reynolds number
    epsilon  : roughness (ft)
    velocity : fpm
    diam     : inches
    """

    def colebrook_white(f):
        return (
            1 / np.sqrt(f)
            + 2 * np.log10(
                (SHEET_METAL_EPSILON / (diam / 12)) / 3.7
                + 2.51 / (re * np.sqrt(f))
            )
        )

    # Solve for Darcy friction factor
    f = fsolve(colebrook_white, initial_guess)[0]

    # Darcy–Weisbach pressure loss
    pressure_loss = 12 * f * duct_length * AIR_DENSITY / diam * (velocity / 1097) ** 2

    return round(pressure_loss, 3)
