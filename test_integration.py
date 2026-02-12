
from src.core.atlas14 import Atlas14Fetcher
from src.core.generator import RainfallGenerator

def test_integration():
    print("Testing Integration...")
    
    # 1. Fetch Data (mock or real)
    # We'll try real since we verified curl works
    print("1. Fetching Data for Houston...")
    fetcher = Atlas14Fetcher()
    try:
        data = fetcher.fetch_data(29.7604, -95.3698)
        print("   Fetch Success.")
        print(f"   60m: {data['60m_25yr']}")
        print(f"   24h: {data['24h_25yr']}")
    except Exception as e:
        print(f"   Fetch Failed: {e}")
        return

    # 2. Generator Logic
    print("\n2. Testing Generator Logic...")
    gen = RainfallGenerator()
    
    # Check Ratio
    ratio = gen.calculate_ratio(data['60m_25yr'], data['24h_25yr'])
    print(f"   Ratio: {ratio}")
    
    type_name, proxy_name = gen.suggest_type(ratio)
    print(f"   Result: {type_name} -> {proxy_name}")
    
    # Generate Table
    print("\n3. Generating Hyetograph (SCS Type II)...")
    df = gen.generate(10.0, "SCS Type II (Legacy/Standard)")
    print(f"   Rows generated: {len(df)}")
    print(f"   Total Cumulative: {df['Cumulative Rainfall (in)'].iloc[-1]}")
    
    if len(df) > 200 and abs(df['Cumulative Rainfall (in)'].iloc[-1] - 10.0) < 0.01:
        print("   Verification PASSED.")
    else:
        print("   Verification FAILED.")

if __name__ == "__main__":
    test_integration()
