import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt

def get_tyre_data(tyre_code, tyre_csv):
    """
    Retrieve tyre properties for a specific tyre code.

    Parameters:
    - tyre_code (str): Tyre model/code (e.g., "H49x19.0-22")
    - tyre_csv (str): Path to tyre database CSV

    Returns:
    - dict: Tyre specifications
    """
    tyre_df = pd.read_csv(tyre_csv)
    tyre_row = tyre_df[tyre_df["tyre_code"] == tyre_code]

    if tyre_row.empty:
        raise ValueError(f"Tyre code '{tyre_code}' not found in database.")

    return tyre_row.iloc[0].to_dict()

def compute_full_stroke_from_reaction_factor(
    mass, lambda_val, V, tyre_data, n_tyres,
    eta_a=0.80, eta_t=0.47, g=9.81
):
    # Tyre parameters
    r_max_in = float(tyre_data["do_max_in"]) / 2
    r_min_in = float(tyre_data["static_radius_max_in"])
    rated_load_lbs = float(str(tyre_data["rated_load_lbs"]).replace(",", ""))
    load_rating = rated_load_lbs * 4.44822

    # Radii in metres
    r_max = r_max_in * 0.0254
    r_min = r_min_in * 0.0254

    # Tyre stroke
    x_t = (0.9 * lambda_val * g * mass * (r_max - r_min)) / (load_rating * n_tyres)

    # Shock absorber stroke
    x_a = (V**2) / (2 * g * eta_a * lambda_val) - (eta_t / eta_a) * x_t

    # Total stroke
    x_total = x_t + x_a

    return x_t, x_a, x_total

def compute_stroke_breakdown_from_lambdas(
    mtom, mlm,
    mlg_lambda, nlg_lambda,
    nlg_mass_fraction,
    mlg_tyre_data, nlg_tyre_data,
    n_mlg_tyres, n_nlg_tyres
):
    results = []

    for V, total_mass in zip([1.83, 3.05, 3.7], [mtom, mlm, mlm]):
        mlg_mass = total_mass * (1 - nlg_mass_fraction)
        nlg_mass = total_mass * nlg_mass_fraction

        # Main gear
        x_t_mlg, x_a_mlg, x_total_mlg = compute_full_stroke_from_reaction_factor(
            mlg_mass, mlg_lambda, V, mlg_tyre_data, n_mlg_tyres
        )

        # Nose gear
        x_t_nlg, x_a_nlg, x_total_nlg = compute_full_stroke_from_reaction_factor(
            nlg_mass, nlg_lambda, V, nlg_tyre_data, n_nlg_tyres
        )

        results.append({
            "V [m/s]": V,
            "Mass [kg]": total_mass,
            "MLG x_t [m]": x_t_mlg,
            "MLG x_a [m]": x_a_mlg,
            "MLG x_total [m]": x_total_mlg,
            "NLG x_t [m]": x_t_nlg,
            "NLG x_a [m]": x_a_nlg,
            "NLG x_total [m]": x_total_nlg,
        })

    return pd.DataFrame(results)

def oleo_pneumatic_sizing(
    ramp_mass_kg,
    landing_mass_kg,
    load_fraction,
    reaction_factor,
    shock_absorber_travel_m,
    breakout_load_fraction,
    static_pressure,
    num_gear_legs,
    max_load_factor,
    limit_stroke_m,
    gravity=9.81
):
    """
    Compute main oleo-pneumatic shock absorber sizing values based on aircraft mass and configuration.
    """
    # Forces supported per main landing gear
    ramp_force_total = ramp_mass_kg * gravity * load_fraction
    landing_force_total = landing_mass_kg * gravity * load_fraction

    force_per_gear_ramp = ramp_force_total / num_gear_legs
    force_per_gear_landing = landing_force_total / num_gear_legs

    # Breakout load based on landing static load
    breakout_load = breakout_load_fraction * force_per_gear_landing

    # Calculate piston area
    A_piston = force_per_gear_ramp / static_pressure
    d_piston = (4 * A_piston / math.pi) ** 0.5

    # Load the seal database
    seal_db = pd.read_csv("data/AS4716_seal_db.csv")

    # Convert piston diameter to inches
    d_piston_in = d_piston * 39.3701

    # Find first seal where B dimension is larger than d_piston
    matching_seal = seal_db[seal_db["C"] > d_piston_in].iloc[0]

    # Extract relevant data
    selected_B_in = matching_seal["C"]
    selected_B = selected_B_in / 39.3701  # convert back to meters
    d_corrected = selected_B

    # Calculate corrected static pressure
    A_piston_corrected = (np.pi * d_corrected ** 2) / 4
    P_static_corrected = force_per_gear_ramp / A_piston_corrected

    # Breakout pressure
    P_0 = breakout_load / A_piston_corrected
    P_1 = P_static_corrected
    P_2 = max_load_factor * force_per_gear_ramp / A_piston_corrected

    # Maximum loads
    P_max_ground_handling = max_load_factor * P_1
    P_max_landing = reaction_factor * P_1

    # Fully extended volume
    V_0 = (A_piston_corrected * shock_absorber_travel_m * P_2) / (P_2 - P_0)
    V_2 = V_0 - (A_piston_corrected * shock_absorber_travel_m)

    # Static position volume and compression
    V_1 = V_0 * P_0 / P_1
    x_static = (V_0 - V_1) / A_piston_corrected

    # Generate spring curve (isothermal)
    n_points = 100
    x = np.linspace(0, shock_absorber_travel_m, n_points)
    V = V_0 - A_piston_corrected * x
    P = P_0 * V_0 / V

    print('Compression ratio: %.2f' % (V_0 / V_2))

    # Plot
    plt.figure(figsize=(9, 6))
    plt.plot(x * 1000, P / 1e6)
    plt.axvline(x=x_static * 1000, color='red', linestyle='--')
    plt.text(x_static * 1000 + 10, (P_1 / 1e6) / 2, f"Static Pos.\n{x_static * 1000:.1f} mm", color='red')

    # Add maximum load lines
    plt.axhline(y=P_max_ground_handling / 1e6, color='blue', linestyle='--')
    plt.text(5, (P_max_ground_handling / 1e6) + 0.2, "Max GH Load", color='blue')

    plt.axhline(y=P_max_landing / 1e6, color='green', linestyle='--')
    plt.text(5, (P_max_landing / 1e6) + 0.2, "Max Landing Load", color='green')

    # Add limit landing stroke
    plt.axvline(x=limit_stroke_m * 1000, color='purple', linestyle='--')
    plt.text(limit_stroke_m * 1000 + 10, 18, "Limit Stroke", color='purple', rotation=90, verticalalignment='center')

    plt.xlabel("Shock Absorber Compression (mm)")
    plt.ylabel("Gas Pressure (MPa)")
    plt.title("Oleo-Pneumatic Spring Curve (Isothermal)")
    plt.grid(True)

    # Add information box
    textstr = '\n'.join((
        f'Breakout Pressure: {P_0 / 1e6:.2f} MPa',
        f'Static Pressure: {P_1 / 1e6:.2f} MPa',
        f'Max Pressure: {P_2 / 1e6:.2f} MPa',
        f'Compression Ratio: {V_0 / V_2:.2f}',
        f'Piston Diameter: {d_corrected*1000:.1f} mm'
    ))

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    plt.gca().text(0.05, 0.95, textstr, transform=plt.gca().transAxes, fontsize=10,
                   verticalalignment='top', horizontalalignment='left', bbox=props)

    plt.tight_layout()
    plt.show()
    return P_0, P_1, P_2, x_static, d_corrected