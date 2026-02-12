import numpy as np
import pandas as pd

# Data from NEH Part 630, Chapter 4, Figure 4-72 (Page 66)
# Mean Ratios for Four Rainfall Distribution Regions (NOAA Atlas 14)
# Ratio of Duration Depth to 24-Hour Depth
# Duration (hours): Ratio
# Note: These are NOT cumulative time ratios. They are depth ratios.
# We need to convert "Ratio of X-hour depth to 24-hour depth" into a temporal distribution.
# The NEH describes the method: "The 24-hour rainfall distribution has the maximum 5-minute rainfall occurring from 12 to 12.1 hours... The maximum 10-minute rainfall is between 11.9 and 12.1 hours..."
# This is a balanced/nested storm approach (like SCS Type II).

# Control Points (Duration in Hours -> Ratio)
# 0 hours is 0 ratio
CONTROL_POINTS = {
    "Region A": {
        0.0833: 0.143, # 5 min
        0.1667: 0.219, # 10 min
        0.25: 0.272,   # 15 min
        0.5: 0.386,    # 30 min
        1.0: 0.502,    # 60 min
        2.0: 0.594,    # 2 hr - Wait, Fig 4.72 says 120-min is 0.594, then 3-hr is 0.635
        3.0: 0.635,
        6.0: 0.749,
        12.0: 0.864,
        24.0: 1.0
    },
    "Region B": {
        0.0833: 0.121,
        0.1667: 0.189,
        0.25: 0.237,
        0.5: 0.344,
        1.0: 0.453,
        2.0: 0.543,
        3.0: 0.585,
        6.0: 0.705,
        12.0: 0.840,
        24.0: 1.0
    },
    "Region C": {
        0.0833: 0.105,
        0.1667: 0.166,
        0.25: 0.210,
        0.5: 0.308,
        1.0: 0.409,
        2.0: 0.500,
        3.0: 0.545,
        6.0: 0.672,
        12.0: 0.823,
        24.0: 1.0
    },
    "Region D": {
        0.0833: 0.094,
        0.1667: 0.149,
        0.25: 0.188,
        0.5: 0.276,
        1.0: 0.366,
        2.0: 0.454,
        3.0: 0.501,
        6.0: 0.636,
        12.0: 0.805,
        24.0: 1.0
    }
}

def generate_nested_distribution(ratios):
    """
    Constructs a 24-hour cumulative distribution from intensity-duration ratios.
    Uses the 'Alternating Block' or 'Balanced Storm' method centered at 12 hours.
    
    1. Interpolate depth ratios to get depths for all standard increments (e.g. every 6 mins).
       However, we only have specific durations. Better to interpolate the D-vs-Ratio curve first.
    """
    
    # Durations we want to solve for: 0 to 24 hours
    # We will step by 0.1 hours (6 minutes)
    # But first we need a smooth Duration-vs-DepthRatio curve
    
    sorted_durations = sorted(ratios.keys())
    known_x = [0] + sorted_durations
    known_y = [0] + [ratios[d] for d in sorted_durations]
    
    # Interpolate to get Ratio for every 0.1 hr duration (up to 24)
    # Using simple linear interpolation for robustness, or PCHIP if available (using numpy interp here)
    # The curve is typically log-ish. 
    # Let's simple interp for now.
    
    dt = 0.1 # 6 min
    max_t = 24.0
    time_steps = np.arange(dt, max_t + dt/2, dt) # 0.1, 0.2 ... 24.0
    
    # Interpolate "Depth Ratio" for each duration
    # This tells us: "In the most intense X hours, Y% of rain falls"
    depth_ratios = np.interp(time_steps, known_x, known_y)
    
    # Now arrange into a balanced storm centered at 12.0
    # Center = 12.0
    # 0.1 hr duration (most intense) at 12.0
    # 0.2 hr duration centered at 12.0 (11.9 to 12.1)
    
    # We build the cumulative hyetograph
    distribution = np.zeros(len(time_steps) + 1) # 0.0 to 24.0
    distribution_times = np.concatenate(([0], time_steps))
    
    # Center index
    center_idx = int(12.0 / dt) # 120
    
    # The depth for the smallest interval (0.1) goes at the center
    # But wait, we need incremental depths.
    
    # Calculate Incremental Ratios for the balanced storm
    # Duration D_i: Total Depth Y_i
    # Duration D_{i-1}: Total Depth Y_{i-1}
    # The extra rain (Y_i - Y_{i-1}) splits to the left and right of the existing block
    
    # Let's build it outward from 12 hours
    # We have depth_ratios for duration 0.1, 0.2, 0.3... 24.0
    
    # Create an array of rainfall depths (relative to 1.0 total)
    # Initialize with 0
    final_cum = np.zeros(len(distribution_times))
    
    # Midpoint is 12.0 hours. 
    # Let's identify the time slots. 
    # slot 0: 0.0-0.1, ..., slot 119: 11.9-12.0, slot 120: 12.0-12.1
    
    # This is effectively the "Alternating Block Method"
    # 1. Calculate intensity/depth for each duration d
    # 2. Calculate incremental depth = Depth(d) - Depth(d-dt)
    # 3. Place largest increment at peak, next largest to right, next to left...
    
    # Interpolate depths for durations: 0.1, 0.2, 0.3 ... 24.0
    interp_durations = np.arange(0.1, 24.05, 0.1)
    interp_depths = np.interp(interp_durations, known_x, known_y)
    
    # Incremental depths between envelopes
    # Depth of 0.1 hr center block = interp_depths[0]
    # Depth of 0.2 hr center block = interp_depths[1]. 
    # The added rain is interp_depths[1] - interp_depths[0]. This added rain is split? 
    # Standard SCS is nested. 
    # Maximum 6-min intensity is at 12.0.
    
    # Simplified Nesting:
    # 12.0 hr = 0.5 (accumulated) ??? No, 24hr is 1.0 accumulated.
    # At 12.0 hours in the cumulative distribution, we are at 50%?? Not necessarily.
    # Wait, SCS Type II is centered. 50% volume is NOT at 12hr. 
    # But the PEAK is at 12hr.
    
    # Let's map "Duration Centered" to "Cumulative Fraction"
    # Center = 12.0
    # For a duration 'd' (e.g. 1 hour), it covers 11.5 to 12.5.
    # The amount of rain in that hour is Ratio(1.0).
    # So Cumulative(12.5) - Cumulative(11.5) = Ratio(1.0)
    
    # Symmetry Assumption (NEH 630.0407 B (ii) bullet 1 says: "Since the preliminary rainfall distribution is symmetrical about 12 hours...")
    # So: Cumulative(12 + d/2) = 0.5 + Ratio(d)/2
    #     Cumulative(12 - d/2) = 0.5 - Ratio(d)/2
    
    # This is a HUGE simplification but it's what the NEH example implies for the preliminary distribution.
    # Let's proceed with this symmetrical assumption as a starting point for "Official" types.
    # It says "Preliminary"... then they skew it? 
    # For now, a symmetrical distribution derived from official ratios is vastly superior to a proxy.
    
    final_dist = {}
    final_dist[0.0] = 0.0
    final_dist[24.0] = 1.0
    final_dist[12.0] = 0.5
    
    for d in interp_durations:
        ratio = d # ratio of duration?? No, 'interp_depths' is the ratio of depth.
        depth_ratio = np.interp(d, known_x, known_y)
        
        t_end = 12.0 + (d / 2.0)
        t_start = 12.0 - (d / 2.0)
        
        # Symmetrical distribution of depth
        if t_end <= 24.0:
            final_dist[t_end] = 0.5 + (depth_ratio / 2.0)
        if t_start >= 0.0:
            final_dist[t_start] = 0.5 - (depth_ratio / 2.0)
            
    # Sort and fill gaps
    times = sorted(final_dist.keys())
    fractions = [final_dist[t] for t in times]
    
    # We want exact 0.1 hr steps
    target_times = np.arange(0.0, 24.05, 0.1)
    target_fractions = np.interp(target_times, times, fractions)
    
    # Round to 4 decimals
    target_fractions = np.round(target_fractions, 4)
    
    return dict(zip(target_times, target_fractions))

# Generate the dicts
output_str = "NOAA_ATLAS_14_DISTRIBUTIONS = {\n"

for region, points in CONTROL_POINTS.items():
    dist = generate_nested_distribution(points)
    
    # Format as python dict code
    output_str += f'    "{region}": {{\n'
    keys = sorted(dist.keys())
    # Downsample for the definition file to keep it manageable? 
    # Or keep all 240 points? Definitions file can handle it.
    # Let's keep 0.5 hr intervals for the static definition to match existing style, 
    # BUT generator interpolates anyway. 
    # Better: Keep critical points (control points) and let generator do the heavy lifting?
    # No, the request asked for "preset excel table". I should calculate the full table.
    
    # Writing full 0.1 hr resolution might be too much text for one tool call.
    # Let's write 0.5 hr resolution + the specific control points from the NEH.
    
    key_points = [0.0, 24.0]
    # Add 0.5 hr steps
    for t in np.arange(0, 24.1, 0.5):
        key_points.append(round(t, 1))
    
    key_points = sorted(list(set(key_points)))
    
    for t in key_points:
        output_str += f"        {t:.1f}: {dist[t]:.4f},\n"
    output_str += "    },\n"

output_str += "}"

print(output_str)
