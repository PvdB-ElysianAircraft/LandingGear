import numpy as np
import matplotlib.pyplot as plt

# Inputs
turn_radius_m = 45.0         # Desired cockpit/cockpit gear turn radius (m)
turn_total_angle_deg = 180.0  # Total turn angle
speed_mps = 5.0              # Constant forward speed (m/s)
dt = 0.01                    # Small time step
taxiway_width_m = 23.0        # Taxiway width (m)

# Gear geometry
wheelbase_m = 14.6        # Distance from main gear to nose gear (A350-900)
CMG_m = 16.6
main_gear_track_m = 15    # Main gear total track width (m)

# Derived parameters
turn_total_angle_rad = np.deg2rad(turn_total_angle_deg)
omega_radps = speed_mps / turn_radius_m   # cockpit gear yaw rate
t_turn = turn_total_angle_rad / omega_radps

# Timing
t_straight_before = 10  # seconds straight before turn
t_straight_after = 30   # extended seconds after turn
t_total = t_straight_before + t_turn + t_straight_after
time = np.arange(0, t_total + dt, dt)

# Initialize lists
x_cockpit = []
y_cockpit = []
psi_cockpit = []

x_main = []
y_main = []
heading_main = []

x_main_left = []
y_main_left = []
x_main_right = []
y_main_right = []

x_nose = []
y_nose = []

# Start positions
x_cp = 0.0
y_cp = 0.0
heading_cp = np.pi/2  # cockpit facing north

# Main gear starts CMG_m behind cockpit gear
x_m = x_cp - CMG_m * np.cos(heading_cp)
y_m = y_cp - CMG_m * np.sin(heading_cp)

# Main gear starts CMG_m behind cockpit gear
x_n = x_cp - (CMG_m-wheelbase_m) * np.cos(heading_cp)
y_n = y_cp - (CMG_m-wheelbase_m) * np.sin(heading_cp)

# Simulation loop
for t in time:
    # Determine steering
    if t <= t_straight_before:
        steering_rate = 0.0
    elif t_straight_before < t <= t_straight_before + t_turn:
        steering_rate = -omega_radps  # turning right
    else:
        steering_rate = 0.0

    # Update cockpit gear heading
    heading_cp += steering_rate * dt

    # Update cockpit gear position
    x_cp += speed_mps * dt * np.cos(heading_cp)
    y_cp += speed_mps * dt * np.sin(heading_cp)

    # Store cockpit gear data
    x_cockpit.append(x_cp)
    y_cockpit.append(y_cp)
    psi_cockpit.append(heading_cp)

    # --- Real main gear (following real track) ---
    delta_x = x_cp - x_m
    delta_y = y_cp - y_m
    heading_m = np.arctan2(delta_y, delta_x)
    heading_main.append(heading_m)

    # Update real main gear position by projection (rigid wheelbase)
    x_m = x_cp - CMG_m * np.cos(heading_m)
    y_m = y_cp - CMG_m * np.sin(heading_m)

    x_n = x_cp - (CMG_m-wheelbase_m) * np.cos(heading_m)
    y_n = y_cp - (CMG_m-wheelbase_m) * np.sin(heading_m)

    x_main.append(x_m)
    y_main.append(y_m)

    x_nose.append(x_n)
    y_nose.append(y_n)

    # Calculate left and right main gear wheels
    half_track = main_gear_track_m / 2
    x_ml = x_m - half_track * np.sin(heading_m)
    y_ml = y_m + half_track * np.cos(heading_m)
    x_mr = x_m + half_track * np.sin(heading_m)
    y_mr = y_m - half_track * np.cos(heading_m)

    x_main_left.append(x_ml)
    y_main_left.append(y_ml)
    x_main_right.append(x_mr)
    y_main_right.append(y_mr)

# Convert to arrays
x_cockpit = np.array(x_cockpit)
y_cockpit = np.array(y_cockpit)
psi_cockpit = np.array(psi_cockpit)
x_main = np.array(x_main)
y_main = np.array(y_main)
heading_main = np.array(heading_main)
x_main_left = np.array(x_main_left)
y_main_left = np.array(y_main_left)
x_main_right = np.array(x_main_right)
y_main_right = np.array(y_main_right)
x_nose = np.array(x_nose)
y_nose = np.array(y_nose)

# --- Simulate Ideal Main Gear Centre Path (Independent Simulation) ---

# Adjusted timing
lag_distance = CMG_m  # 30.26 m
lag_time = lag_distance / speed_mps  # time lag (seconds)

t_straight_before_ideal = t_straight_before + lag_time
t_straight_after_ideal = t_total - (t_straight_before_ideal + t_turn)

# Rebuild ideal path
x_main_ideal = []
y_main_ideal = []
heading_ideal = []

# Start position for ideal main gear
x_m_ideal = x_main[0]
y_m_ideal = y_main[0]
heading_ideal_current = np.pi/2  # facing north

for t_now in time:
    if t_now <= t_straight_before_ideal:
        steering_rate = 0.0
    elif t_straight_before_ideal < t_now <= t_straight_before_ideal + t_turn:
        steering_rate = -omega_radps
    else:
        steering_rate = 0.0

    heading_ideal_current += steering_rate * dt
    x_m_ideal += speed_mps * dt * np.cos(heading_ideal_current)
    y_m_ideal += speed_mps * dt * np.sin(heading_ideal_current)

    x_main_ideal.append(x_m_ideal)
    y_main_ideal.append(y_m_ideal)
    heading_ideal.append(heading_ideal_current)

# Convert to arrays
x_main_ideal = np.array(x_main_ideal)
y_main_ideal = np.array(y_main_ideal)

# --- Taxiway edges based on cockpit gear path ---
offset = taxiway_width_m / 2
x_left = x_cockpit - offset * np.sin(psi_cockpit)
y_left = y_cockpit + offset * np.cos(psi_cockpit)
x_right = x_cockpit + offset * np.sin(psi_cockpit)
y_right = y_cockpit - offset * np.cos(psi_cockpit)

# Extend taxiway downward manually
x_left = np.insert(x_left, 0, x_left[0])
y_left = np.insert(y_left, 0, y_left[0] - 40)
x_right = np.insert(x_right, 0, x_right[0])
y_right = np.insert(y_right, 0, y_right[0] - 40)

# Create taxiway polygon
x_polygon = np.concatenate([x_left, x_right[::-1]])
y_polygon = np.concatenate([y_left, y_right[::-1]])

# --- Plotting ---
plt.figure(figsize=(12,12))
plt.fill(x_polygon, y_polygon, color='lightgrey', alpha=0.5, label='Taxiway')
plt.plot(x_left, y_left, color='black', linewidth=0.5)
plt.plot(x_right, y_right, color='black', linewidth=0.5)

# Plot paths
plt.plot(x_cockpit, y_cockpit, color='blue', label='Cockpit path (centreline)')
plt.plot(x_nose, y_nose, color='yellow', label='NLG path')
plt.plot(x_main, y_main, color='red', label='MLG centre path')
plt.plot(x_main_left, y_main_left, 'r--', label='MLG inner tyre path')
plt.plot(x_main_right, y_main_right, 'r:', label='MLG outer tyre path')
# plt.plot(x_main_ideal, y_main_ideal, 'g--', label='Ideal main gear centre path')


# Plot T-shapes every 10 seconds
for idx, t_now in enumerate(time):
    if np.isclose(t_now % 10, 0, atol=dt/2):
        x_cp_current = x_cockpit[idx]
        y_cp_current = y_cockpit[idx]
        x_m_current = x_main[idx]
        y_m_current = y_main[idx]
        psi_m_current = heading_main[idx]

        x_m_left = x_m_current - half_track * np.sin(psi_m_current)
        y_m_left = y_m_current + half_track * np.cos(psi_m_current)
        x_m_right = x_m_current + half_track * np.sin(psi_m_current)
        y_m_right = y_m_current - half_track * np.cos(psi_m_current)

        plt.plot([x_cp_current, x_m_current], [y_cp_current, y_m_current], color='black', linewidth=0.8)
        plt.plot([x_m_left, x_m_right], [y_m_left, y_m_right], color='black', linewidth=0.8)

# Final plot settings
plt.gca().set_aspect('equal')
plt.grid(True)
plt.xlabel('X (m)')
plt.ylabel('Y (m)')
# plt.title('Realistic Aircraft Turn with Time-Lagged Ideal Main Gear Path')
plt.legend()
# plt.savefig('aircraft_turn_tracks.png', dpi=300, transparent=True, bbox_inches='tight')

# --- Calculate off-tracking between real and ideal main gear centres ---

off_tracking = np.sqrt((x_main - x_main_ideal)**2 + (y_main - y_main_ideal)**2)
max_off_tracking = np.max(off_tracking)

print(f"Maximum off-tracking between real and ideal main gear: {max_off_tracking:.2f} meters")

# --- Plot off-tracking vs time ---
plt.figure(figsize=(10,5))
plt.plot(time, off_tracking, label='Off-tracking (real vs ideal)')
plt.grid(True)
plt.xlabel('Time (s)')
plt.ylabel('Off-tracking distance (m)')
plt.title('Off-Tracking Distance Over Time')
plt.legend()
plt.show()

print('test')