import subprocess
import shutil
import csv
import io
import re

class Atlas14Fetcher:
    """
    Fetches precipitation frequency estimates from NOAA Atlas 14 via their CSV endpoint.
    Uses 'curl' via subprocess to bypass SSL handshake issues on some systems.
    """
    
    BASE_URL = "https://hdsc.nws.noaa.gov/cgi-bin/hdsc/new/fe_text_mean.csv"
    
    def __init__(self):
        # Verify curl is available
        if not shutil.which("curl"):
            raise EnvironmentError("The 'curl' command is required but not found in PATH.")

    def fetch_data(self, lat, lon, return_period_years=100):
        """
        Fetches precipitation frequency estimates for the given lat/lon.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            return_period_years (int): Return period to extract the 24h depth for generation (default 100).
            
        Returns:
            dict: {
                "24h_25yr": float,
                "60m_25yr": float, 
                "24h_selected": float,  # Depth for the selected return period (e.g. 100yr)
                "raw_csv": str          # Full CSV content for reference or further parsing
            }
        """
        # Construct URL with parameters
        # data=depth, units=english, series=pds (partial duration series)
        url = f"{self.BASE_URL}?lat={lat}&lon={lon}&data=depth&units=english&series=pds"
        
        print(f"Fetching data from: {url}")
        
        try:
            # -L: Follow redirects
            # -k: Insecure (skip SSL verification due to potential local handshake issues)
            # -s: Silent (no progress bar)
            process = subprocess.run(
                ["curl", "-L", "-k", "-s", url], 
                capture_output=True, 
                text=True,
                check=True
            )
            
            content = process.stdout
            
            if "File not found" in content or "Error" in content and len(content) < 200:
                raise ValueError("NOAA Atlas 14 returned an error or no data for this location.")
                
            return self._parse_csv(content, return_period_years)
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to fetch data via curl: {e}")
        except Exception as e:
            raise RuntimeError(f"Error fetching data: {e}")

    def _parse_csv(self, csv_content, target_return_period):
        """
        Parses the CSV content to extract specific depths.
        """
        lines = csv_content.splitlines()
        reader = csv.reader(lines)
        
        header_map = {}
        data_map = {} # duration -> {return_period: depth}
        
        parsing_data = False
        
        for row in reader:
            if not row: continue
            
            # Identify the header row
            if "by duration for ARI (years):" in row[0]:
                parsing_data = True
                # Map return periods to column indices
                # Row looks like: ["by duration...", "1", "2", "5", "10", "25", ...]
                for i, cell in enumerate(row):
                    if i == 0: continue
                    try:
                        rp = int(cell.strip())
                        header_map[rp] = i
                    except ValueError:
                        continue
                continue
            
            if parsing_data:
                # Parse data rows
                # Row looks like: ["60-min:", "1.5", "1.8", ...]
                duration_label = row[0].strip().replace(":", "")
                
                # normalize labels (60-min, 24-hr)
                if "min" in duration_label:
                    key = duration_label
                elif "hr" in duration_label:
                    key = duration_label
                elif "day" in duration_label:
                    key = duration_label
                else:
                    continue
                    
                data_map[key] = {}
                
                for rp, col_idx in header_map.items():
                    if col_idx < len(row):
                        try:
                            val = float(row[col_idx])
                            data_map[key][rp] = val
                        except ValueError:
                            pass
        
        # Extract required values
        # We need 25-yr 60-min and 25-yr 24-hr
        try:
            d60m_25yr = data_map.get("60-min", {}).get(25, 0.0)
            d24h_25yr = data_map.get("24-hr", {}).get(25, 0.0)
            d24h_selected = data_map.get("24-hr", {}).get(target_return_period, 0.0)
            
            if d24h_25yr == 0:
                raise ValueError("Could not find 24-hr 25-yr depth in data.")

            return {
                "24h_25yr": d24h_25yr,
                "60m_25yr": d60m_25yr,
                "24h_selected": d24h_selected,
                "full_data": data_map, # Return all parsed data
                "raw_csv": csv_content
            }
            
        except Exception as e:
            raise ValueError(f"Failed to parse required data from CSV: {e}")

if __name__ == "__main__":
    # Test
    fetcher = Atlas14Fetcher()
    try:
        data = fetcher.fetch_data(29.7604, -95.3698) # Houston
        print("Success:", data)
    except Exception as e:
        print("Failed:", e)
