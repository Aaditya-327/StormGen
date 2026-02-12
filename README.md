# NOAA Atlas 14 Rainfall Generator

A Python desktop application for generating 24-hour rainfall hyetographs using official NOAA Atlas 14 precipitation frequency estimates.

## Overview

This tool automates the process of creating design storms for hydrologic modeling. It fetches point-specific rainfall depths from the NOAA Precipitation Frequency Data Server (PFDS) and generates a time-series distribution based on the characteristics of the rainfall (60-minute vs 24-hour depth ratio).

## Features

-   **Automated Data Fetching**: Retrieves 25-year (and other) rainfall depths directly from NOAA using site-specific coordinates.
-   **Smart Pattern Selection**: Automatically suggests the appropriate rainfall distribution type (A, B, C, or D) based on the calculated rainfall ratio ($r = D_{60m} / D_{24h}$).
-   **Standard Distributions**: Includes standard SCS Type I, IA, II, and III distributions.
-   **Interactive Map**: built-in Leaflet map for easy location selection.

## Installation & Usage

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Requires Python 3.9+, PyQt5, pandas, matplotlib, requests (or curl).*

2.  **Run the Application**:
    ```bash
    python main.py
    ```

3.  **Workflow**:
    *   **Select Location**: Click on the map or enter Latitude/Longitude.
    *   **Fetch Data**: Click "Fetch NOAA Data" to retrieve official depths.
    *   **Review Recommendation**: The specific NOAA region type (A, B, C, D) is calculated and displayed.
    *   **Generate**: Choose "Auto-Select" to use the recommended proxy, or manually select a distribution.

## Logic & Defaults

### The "Auto-Select" Logic
Modern hydrology (NOAA Atlas 14) moves away from the single "Type II" storm for the entire country. instead, it uses regionalized temporal distributions (Types A, B, C, D) based on the ratio of short-duration to long-duration rainfall.

This application implements this logic:
1.  **Fetch**: 25-year 60-minute and 24-hour depths are fetched.
2.  **Calculate Ratio**: $r = \frac{60min Depth}{24hr Depth}$
3.  **Classify**:
    *   **Type A** ($r < 0.30$): Least intense peak. *Proxy: SCS Type I.*
    *   **Type B** ($0.30 \le r < 0.35$): Moderate intensity. *Proxy: SCS Type II.*
    *   **Type C** ($0.35 \le r < 0.40$): High intensity. *Proxy: SCS Type III.*
    *   **Type D** ($r \ge 0.40$): Extreme intensity. *Proxy: SCS Type III.*

### Why "Proxy"? (Important Caveat)
**BE CAREFUL:** While the app correctly identifies the *NOAA Type* (e.g., "Type B"), the exact tabular 6-minute values for NOAA A/B/C/D are highly specific to state/county regulations (often found in restricted PDF manuals like Virginia DEQ).

To ensure the app works out-of-the-box everywhere, **this application uses standard SCS (Legacy) distributions as proxies** for these types.
*   **SCS Type II** is a conservative, standard proxy for **Type B**.
*   **SCS Type III** is used for **Type C/D**.

**If your project requires strict regulatory compliance with a specific state manual (e.g., "Virginia DEQ Chapter 10"), you should:**
1.  Obtain the exact cumulative fraction table from your local manual.
2.  Select **"Custom"** in the dropdown.
3.  (Future Feature) Paste your specific distribution table.

## Warning Limits

*   **Legacy vs. Modern**: SCS Type II is a "nested" storm and is often **more conservative** (higher peak flow) than the actual NOAA Atlas 14 distributions. Using it is generally "safe" but might lead to larger-than-necessary detention ponds.
*   **Data Source**: The app scrapes the NOAA PFDS. If NOAA changes their website structure, the fetcher may need updating.
