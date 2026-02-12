import subprocess
import shutil

def test_fetch():
    # Try the CSV endpoint found in pfdf source
    url = "https://hdsc.nws.noaa.gov/cgi-bin/hdsc/new/fe_text_mean.csv?lat=29.7604&lon=-95.3698&data=depth&units=english&series=pds"
    
    print(f"Fetching {url} using curl...")
    try:
        # Use curl to fetch data
        if not shutil.which("curl"):
            print("Error: curl not found")
            return

        result = subprocess.run(
            ["curl", "-L", "-k", url], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            print(f"Curl failed with code {result.returncode}")
            print(result.stderr)
            return

        print(f"Curl success. Content length: {len(result.stdout)}")
        print("--- First 500 chars ---")
        print(result.stdout[:500])
        
        # Save to file for inspection
        with open("debug_noaa_response.html", "w") as f:
            f.write(result.stdout)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_fetch()
