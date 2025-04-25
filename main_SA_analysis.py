
import pandas as pd

from functions import compute_reaction_factors_for_aircraft

df = compute_reaction_factors_for_aircraft(
    aircraft_name="A320",
    x_a_main=0.50,
    x_a_nose=0.50,
    aircraft_csv="data/aircraft_db.csv",
    tyre_csv="data/tyre_db.csv",
    nose_gear_mass_fraction=0.15
)

print(df)

