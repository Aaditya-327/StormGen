# NOAA Atlas 14 Rainfall Generator

A Python desktop application for generating 24-hour rainfall hyetographs using official NOAA Atlas 14 precipitation frequency estimates.

## Overview

This tool automates the process of creating design storms for hydrologic modeling. It fetches point-specific rainfall depths from the NOAA Precipitation Frequency Data Server (PFDS) and generates a time-series distribution based on the characteristics of the rainfall (60-minute vs 24-hour depth ratio).

## Features

-   **Automated Data Fetching**: Retrieves 25-year (and other) rainfall depths directly from NOAA using site-specific coordinates.
-   **Smart Pattern Selection**: Automatically suggests the appropriate rainfall distribution type (A, B, C, or D) based on the calculated rainfall ratio ($r = D_{60m} / D_{24h}$).
-   **Standard Distributions**: Includes standard SCS Type I, IA, II, and III distributions.
-   **Interactive Map**: built-in Leaflet map for easy location selection.

![App Screenshot](assets/app_screenshot.png)

*The NOAA Atlas 14 Rainfall Generator main interface, showing the interactive map selection, rainfall generation parameters, and the newly added Atlas 14 data table tab.*

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

## Data Sources & Documentation

This application relies on two primary official sources:

1.  **Rainfall Depths (Precipitation Frequency)**: Fetched directly from the **NOAA Atlas 14** Precipitation Frequency Data Server (PFDS).
    *   **API Endpoint**: `https://hdsc.nws.noaa.gov/cgi-bin/hdsc/new/fe_text_mean.csv`
    *   **Documentation**: [NOAA Atlas 14 Documents](https://www.nws.noaa.gov/ohd/hdsc/PF_documents/Atlas14_Volume1.pdf)
2.  **Temporal Distributions (Hyetograph Shapes)**: Based on the **USDA NRCS National Engineering Handbook (NEH), Part 630, Chapter 4**.
    *   **Reference**: Figure 4-72 (Regionalized Temporal Distributions for Atlas 14).
    *   **Types**: Includes Region A, B, C, and D distributions, as well as legacy SCS Type I, IA, II, and III.



## Logic & Defaults

### The "Auto-Select" Logic
Modern hydrology (NOAA Atlas 14) uses regionalized temporal distributions (Types A, B, C, D) based on the ratio of short-duration to long-duration rainfall (intensity).

This application automates this selection:
1.  **Calculate Ratio**: $r = \frac{60min Depth}{24hr Depth}$ (fetched from Atlas 14).
2.  **Classify & Apply**:
    *   **Region A** ($r < 0.30$): Slow-rising storm.
    *   **Region B** ($0.30 \le r < 0.35$): Standard moderate storm.
    *   **Region C** ($0.35 \le r < 0.40$): High-intensity peak.
    *   **Region D** ($r \ge 0.40$): Extreme intensity peak.

**Are these "Proxies"?**
No. This tool uses **digitized official coordinates** for Regions A, B, C, and D as defined in the NRCS NEH textbook. Unlike earlier versions that used SCS Type II as a proxy, this version uses the dedicated Atlas 14 regional curves.

### Warning & Compliance
*   **Compliance**: Always verify results against your local regulatory manual (e.g., Virginia DEQ, Texas DOT). Some states have specific variations of these curves.
*   **48-hour Tail**: The generator outputs a 48-hour series where the last 24 hours are zero rainfall. This is standard for detention pond modeling to allow the hydrograph to "draw down."

## Attribution
Made by Aadi Bhattarai (aaditya.r.bhattarai@gmail.com)
Based on NOAA PFDS and USDA NRCS NEH Part 630.
