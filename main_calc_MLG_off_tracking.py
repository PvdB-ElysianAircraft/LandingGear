import math

# Input parameters
lambda_steering = 66.1  # steering angle in degrees
wheelbase_ft = 94.05  # distance between main and nose gear in feet
CMG_ft = 99.27        # distance from turn center to cockpit in feet
OMGWS_ft = 42.22      # main gear track width
turn_radius_ft = 150  # assumed cockpit turn radius
taxiway_width_m = 23  # total taxiway width in meters
turn_angle_deg = 135   # total turn angle, in degrees

# Calculate turn center y-coordinate
y_tc_ft = wheelbase_ft * math.tan(math.radians(90 - lambda_steering))

# Calculate turn radii
nose_gear_turn_radius_ft = math.sqrt(wheelbase_ft**2 + y_tc_ft**2)
nose_gear_turn_radius_m = nose_gear_turn_radius_ft * 0.3048  # ft to m

cockpit_turn_radius_ft = math.sqrt(CMG_ft**2 + y_tc_ft**2)
cockpit_turn_radius_m = cockpit_turn_radius_ft * 0.3048  # ft to m

turn_radius_m = turn_radius_ft * 0.3048  # ft to m (cockpit follows)

# Approximate steady-state off-tracking
wheelbase_m = wheelbase_ft * 0.3048  # ft to m
off_tracking_m = (wheelbase_m**2) / (2 * turn_radius_m)

# Apply sin(theta/2) correction for non-steady-state
turn_angle_rad = math.radians(turn_angle_deg)
off_tracking_corrected_m = off_tracking_m * math.sin(turn_angle_rad / 2)

# Calculate position of outer side of inner tyre
OMGWS_m = OMGWS_ft * 0.3048  # ft to m
position_inner_tyre_outer_edge_m = off_tracking_corrected_m + OMGWS_m / 2

# Margin calculation
half_taxiway_width_m = taxiway_width_m / 2
required_margin_m = 4.0  # required margin to taxiway edge
max_allowed_position_m = half_taxiway_width_m - required_margin_m

if position_inner_tyre_outer_edge_m > max_allowed_position_m:
    extra_fillet_m = position_inner_tyre_outer_edge_m - max_allowed_position_m
else:
    extra_fillet_m = 0.0

# Output
print(f"Turn centre y-coordinate (ft): {y_tc_ft:.2f}")
print(f"Nose gear turn radius (m): {nose_gear_turn_radius_m:.2f}")
print(f"Cockpit turn radius (m): {cockpit_turn_radius_m:.2f}")
print(f"Steady-state approximate off-tracking (m): {off_tracking_m:.2f}")
print(f"Corrected off-tracking for {turn_angle_deg}° turn (m): {off_tracking_corrected_m:.2f}")
print(f"Position of outer side of inner tyre (m): {position_inner_tyre_outer_edge_m:.2f}")
print(f"Required maximum position (m): {max_allowed_position_m:.2f}")
print(f"Extra fillet needed (m): {extra_fillet_m:.2f}")
