import pandas as pd
import numpy as np
from scipy.interpolate import PchipInterpolator
from src.utils.definitions import RAINFALL_DISTRIBUTIONS, NOAA_ATLAS_14_DISTRIBUTIONS

class RainfallGenerator:
    def __init__(self):
        pass

    def calculate_ratio(self, depth_60m, depth_24h):
        """Calculates the 60min/24h ratio."""
        if depth_24h == 0: return 0.0
        return depth_60m / depth_24h

    def suggest_type(self, ratio):
        """
        Suggests a NOAA/NRCS Type based on the ratio.
        Returns a tuple (TypeName, ProxyDistributionName)
        """
        if ratio < 0.30:
            return "Type A", "NOAA Region A"
        elif ratio < 0.35:
            return "Type B", "NOAA Region B"
        elif ratio < 0.40:
             return "Type C", "NOAA Region C"
        else:
            return "Type D", "NOAA Region D"

    def generate(self, total_depth, distribution_name, custom_curve=None):
        """
        Generates 24h rainfall distribution.
        start_time: 2026-01-01 00:00
        interval: 6 min
        
        Args:
            total_depth (float): Total 24h rainfall in inches.
            distribution_name (str): Key in RAINFALL_DISTRIBUTIONS or "Custom".
            custom_curve (dict, optional): {time_hr: fraction} if distribution_name is "Custom".
            
        Returns:
            pd.DataFrame: [Date, Time, Incremental, Cumulative]
        """
        
        # Get the distribution points
        if distribution_name == "Custom" and custom_curve:
            points = custom_curve
        else:
            points = RAINFALL_DISTRIBUTIONS.get(distribution_name)
            if not points:
                points = NOAA_ATLAS_14_DISTRIBUTIONS.get(distribution_name)
            
        if not points:
            raise ValueError(f"Unknown distribution: {distribution_name}")
            
        # Create interpolation function
        # Points are time(hr) -> fraction
        known_times = sorted(points.keys())
        known_fractions = [points[t] for t in known_times]
        
        # Create 6-minute time series (0.1 hr)
        # 0 to 48 hours
        # First 24h is the distribution, next 24h is 0 incremental
        result_times = np.arange(0, 48.1, 0.1) # 0.0, 0.1, ... 48.0
        
        # Interpolate cumulative fractions for first 24h using PCHIP for smoothness and monotonicity
        pchip = PchipInterpolator(known_times, known_fractions)
        fractions_24h = pchip(result_times[result_times <= 24.0])
        
        # Ensure it's clipped between 0 and 1 just in case of tiny precision errors
        fractions_24h = np.clip(fractions_24h, 0, 1)
        
        # Extend fractions to 48h (constant 1.0 after 24h)
        fractions = np.pad(fractions_24h, (0, len(result_times) - len(fractions_24h)), 'edge')
        
        # Calculate depths
        cumulative_depths = fractions * total_depth
        
        # Calculate incremental depths
        # First point is 0, so first interval is depth at 0.1 - depth at 0.0
        incremental_depths = np.diff(cumulative_depths, prepend=0)
        
        # Create DataFrame
        start_date = pd.Timestamp("2026-01-01 00:00")
        timestamps = [start_date + pd.Timedelta(hours=t) for t in result_times]
        
        df = pd.DataFrame({
            "DateTime": timestamps,
            "Hours": result_times,
            "Cumulative Fraction": fractions,
            "Cumulative Rainfall (in)": cumulative_depths,
            "Incremental Rainfall (in)": incremental_depths
        })
        
        # Format columns for display
        df["Date"] = df["DateTime"].dt.date
        df["Time"] = df["DateTime"].dt.time
        
        # Rounding as requested
        # Hours: 1 decimal place
        # Incremental Rainfall: 6 decimal places (no more)
        # Cumulative: Let's match incremental precision or standard 2
        df["Hours"] = df["Hours"].round(1)
        df["Incremental Rainfall (in)"] = df["Incremental Rainfall (in)"].round(6)
        df["Cumulative Rainfall (in)"] = df["Cumulative Rainfall (in)"].round(6) 
        
        # Reorder
        df = df[["Date", "Time", "Hours", "Incremental Rainfall (in)", "Cumulative Rainfall (in)"]]
        
        return df

if __name__ == "__main__":
    gen = RainfallGenerator()
    df = gen.generate(10.0, "SCS Type II")
    print(df.head())
    print(df.tail())
