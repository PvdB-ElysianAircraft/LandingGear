import pandas as pd


def get_aircraft_data(aircraft_name, aircraft_csv):
    """
    Retrieve mass properties and tyre codes for a specific aircraft.

    Parameters:
    - aircraft_name (str): Name of the aircraft (e.g., "A320")
    - aircraft_csv (str): Path to aircraft database CSV

    Returns:
    - dict: Aircraft mass properties and tyre codes
    """
    aircraft_df = pd.read_csv(aircraft_csv)
    aircraft_row = aircraft_df[aircraft_df["name"] == aircraft_name]

    if aircraft_row.empty:
        raise ValueError(f"Aircraft '{aircraft_name}' not found in database.")

    aircraft = aircraft_row.iloc[0]

    return {
        "name": aircraft["name"],
        "mtom": aircraft["mtom"],
        "mlm": aircraft["mlm"],
        "num_main_tyres": aircraft["num_main_tyres"],
        "main_gear_tyre_code": aircraft["main_gear_tyre_code"],
        "nose_gear_tyre_code": aircraft["nose_gear_tyre_code"]
    }


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

def lambda_xt_iter(
    V, x_a, m, r_max_in, r_min_in, load_rating, n_tyres,
    eta_a=0.80, eta_t=0.47, g=9.81, tol=1e-6, max_iter=100
):
    r_max = r_max_in * 0.0254
    r_min = r_min_in * 0.0254
    x_t = 0.1 # initial value
    for _ in range(max_iter):
        lambda_val = V**2 / (2 * g * (eta_a * x_a + eta_t * x_t))
        x_t_new = (0.9 * lambda_val * g * m * (r_max - r_min)) / (load_rating * n_tyres)
        if abs(x_t_new - x_t) < tol:
            break
        x_t = x_t_new
    else:
        raise RuntimeError("Iteration did not converge.")
    return lambda_val, x_t


# Wrapper function
def solve_reaction_factor(tyre_code, mtom, mlm, n_tyres, x_a, tyre_csv):
    tyre = get_tyre_data(tyre_code, tyre_csv)
    r_max_in = float(tyre['do_max_in']) / 2
    r_min_in = float(tyre['static_radius_max_in'])
    rated_load_lbs = float(str(tyre['rated_load_lbs']).replace(",", ""))
    load_rating = rated_load_lbs * 4.44822

    results = []
    for V in [1.83, 3.05, 3.7]:
        m = mtom if V == 1.83 else mlm
        λ, x_t = lambda_xt_iter(V, x_a, m, r_max_in, r_min_in, load_rating, n_tyres)
        results.append({
            "tyre_code": tyre_code,
            "V [m/s]": V,
            "mass [kg]": m,
            "lambda": λ,
            "x_a [m]": x_a,
            "x_t [m]": x_t
        })
    return results

def compute_reaction_factors_for_aircraft(
    aircraft_name,
    x_a_main,
    x_a_nose,
    aircraft_csv,
    tyre_csv,
    nose_gear_mass_fraction=0.15
):
    # Get aircraft data
    aircraft = get_aircraft_data(aircraft_name, aircraft_csv)

    # --- Main Gear ---
    main_results = solve_reaction_factor(
        tyre_code=aircraft["main_gear_tyre_code"],
        mtom=aircraft["mtom"],
        mlm=aircraft["mlm"],
        n_tyres=aircraft["num_main_tyres"],
        x_a=x_a_main,
        tyre_csv=tyre_csv
    )

    # --- Nose Gear ---
    mtom_nose = nose_gear_mass_fraction * aircraft["mtom"]
    mlm_nose = nose_gear_mass_fraction * aircraft["mlm"]

    nose_results = solve_reaction_factor(
        tyre_code=aircraft["nose_gear_tyre_code"],
        mtom=mtom_nose,
        mlm=mlm_nose,
        n_tyres=2,
        x_a=x_a_nose,
        tyre_csv=tyre_csv
    )

    return pd.DataFrame(main_results + nose_results)
