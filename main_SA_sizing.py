import pandas as pd
from functions_SA_sizing import get_tyre_data, compute_stroke_breakdown_from_lambdas, oleo_pneumatic_sizing

# Sizing properties
MTOM = 76000
MLM = 76000
mlg_tyre = "1270x455R22"
nlg_tyre = "30x8.8R15"


mlg_tyre = get_tyre_data(mlg_tyre, "data/tyre_db.csv")
nlg_tyre = get_tyre_data(nlg_tyre, "data/tyre_db.csv")

df = compute_stroke_breakdown_from_lambdas(
    mtom=MTOM,
    mlm=MLM,
    mlg_lambda=1.1,
    nlg_lambda=1.2,
    nlg_mass_fraction=0.15,
    mlg_tyre_data=mlg_tyre,
    nlg_tyre_data=nlg_tyre,
    n_mlg_tyres=4,
    n_nlg_tyres=2
)

# Apply margin to shock absorber strokes
df["Shock Absorber Stroke MLG (with margin)"] = df["MLG x_a [m]"] * 1.20
df["Shock Absorber Stroke NLG (with margin)"] = df["NLG x_a [m]"] * 1.10


# Main gear oleo sizing
_, _, _, _, d_corrected = oleo_pneumatic_sizing(
    ramp_mass_kg=MTOM,
    landing_mass_kg=MLM,
    load_fraction=0.95,
    reaction_factor=1.1,
    shock_absorber_travel_m=0.6,
    num_gear_legs=2,
    max_load_factor = 1.7,
    limit_stroke_m=0.500,
    static_pressure=13.0E6,
    breakout_load_fraction=0.17
)

print('MLG piston diameter: %.2f'%d_corrected)

# Main gear oleo sizing
_, _, _, _, d_corrected = oleo_pneumatic_sizing(
    ramp_mass_kg=MTOM,
    landing_mass_kg=MLM,
    load_fraction=0.15,
    reaction_factor=1.1,
    shock_absorber_travel_m=0.5,
    num_gear_legs=1,
    max_load_factor=2.2,
    limit_stroke_m=0.450,
    static_pressure=13.0E6,
    breakout_load_fraction=0.15
)

print('NLG piston diameter: %.2f'%d_corrected)
