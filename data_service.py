import pandas as pd
import requests
import re
import defusedxml.ElementTree as ET
from datetime import datetime, timedelta
import time
import streamlit as st
import json

# INGV API endpoint for Italian earthquakes
INGV_API_URL = "https://webservices.ingv.it/fdsnws/event/1/query"

# USGS API endpoint for worldwide earthquakes
USGS_API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

# EMSC API endpoint
EMSC_API_URL = "https://www.seismicportal.eu/fdsnws/event/1/query"

# GOSSIP-OV feed (rete locale OV - micro-eventi vulcani campani)
GOSSIP_OV_URL = "https://terremoti.ov.ingv.it/gossip/report.xml"

# Function to fetch earthquake data from INGV (Italian Geological Service)
def fetch_ingv_data():
    # Get earthquakes from the last 7 days
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=7)

    # Format dates for the API request
    start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")
    end_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")

    # Parameters for the INGV API request - using the updated format and parameters
    params = {
        "starttime": start_str,
        "endtime": end_str,
        "minmag": 1.0,  # Minimum magnitude
        "maxlat": 48.0,
        "minlat": 35.0,  # Latitude range for Italy
        "maxlon": 19.0,
        "minlon": 6.0,   # Longitude range for Italy
        "format": "geojson",  # Changed from "json" to "geojson"
        "limit": 500     # Limit the number of results
    }

    try:
        # Add proper headers for the request
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'EarthquakeMonitoringApp/1.0'
        }

        response = requests.get(INGV_API_URL, params=params, headers=headers)

        # Debug info
        st.session_state['debug_info'] = {
            'status_code': response.status_code,
            'url': response.url
        }

        # Check if response is successful
        if response.status_code != 200:
            st.error(f"INGV API Error: Status code {response.status_code}")
            return pd.DataFrame()

        # Check if response contains data
        if not response.text:
            st.error("INGV API returned empty response")
            return pd.DataFrame()

        # Try to parse JSON data
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            st.error(f"Error parsing INGV data: {e}")
            # If there's an issue with JSON parsing, return empty dataframe
            return pd.DataFrame()

        # Process the earthquakes - handle potential different formats
        earthquakes = []

        if "features" in data:
            for event in data.get("features", []):
                props = event.get("properties", {})
                geometry = event.get("geometry", {})
                coordinates = geometry.get("coordinates", [0, 0, 0]) if geometry else [0, 0, 0]

                # Handle both potential time formats
                time_val = props.get("time", "")
                if isinstance(time_val, (int, float)):
                    # If time is provided as Unix timestamp in milliseconds
                    time_str = datetime.fromtimestamp(time_val/1000).strftime("%Y-%m-%dT%H:%M:%S")
                else:
                    # If time is provided as ISO string
                    time_str = time_val

                earthquakes.append({
                    "time": time_str,
                    "magnitude": props.get("mag", 0),
                    "depth": coordinates[2] if len(coordinates) > 2 else 0,
                    "latitude": coordinates[1] if len(coordinates) > 1 else 0,
                    "longitude": coordinates[0] if len(coordinates) > 0 else 0,
                    "location": props.get("place", "Unknown"),
                    "source": "INGV"
                })

        return pd.DataFrame(earthquakes)

    except Exception as e:
        st.error(f"Error fetching INGV data: {e}")
        return pd.DataFrame()

# Function to fetch earthquake data from USGS (US Geological Survey)
def fetch_usgs_data():
    # Get earthquakes from the last 7 days with focus on the Campania region
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=7)

    # Format dates for the API request
    start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")
    end_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")

    # Parameters for the USGS API request
    # Focused on Campania region (Vesuvius & Campi Flegrei)
    params = {
        "format": "geojson",
        "starttime": start_str,
        "endtime": end_str,
        "minmagnitude": 1.0,
        "latitude": 40.85,      # Approximate center of the Campania region
        "longitude": 14.25,
        "maxradiuskm": 100,     # 100km radius around the center
        "limit": 500
    }

    try:
        # Add proper headers for the request
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'EarthquakeMonitoringApp/1.0'
        }

        response = requests.get(USGS_API_URL, params=params, headers=headers)

        # Store debug info
        if 'debug_info' not in st.session_state:
            st.session_state['debug_info'] = {}
        st.session_state['debug_info']['usgs_status_code'] = response.status_code
        st.session_state['debug_info']['usgs_url'] = response.url

        # Check if response is successful
        if response.status_code != 200:
            st.error(f"USGS API Error: Status code {response.status_code}")
            return pd.DataFrame()

        # Check if response contains data
        if not response.text:
            st.error("USGS API returned empty response")
            return pd.DataFrame()

        # Try to parse JSON data
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            st.error(f"Error parsing USGS data: {e}")
            return pd.DataFrame()

        # Process the earthquakes more efficiently
        earthquakes = []
        features = data.get("features", [])
        if features:
            earthquakes = [{
                "time": datetime.fromtimestamp(feature["properties"].get("time", 0)/1000).strftime("%Y-%m-%dT%H:%M:%S"),
                "magnitude": feature["properties"].get("mag", 0),
                "depth": feature["geometry"]["coordinates"][2] if feature.get("geometry") else 0,
                "latitude": feature["geometry"]["coordinates"][1] if feature.get("geometry") else 0,
                "longitude": feature["geometry"]["coordinates"][0] if feature.get("geometry") else 0,
                "location": feature["properties"].get("place", "Unknown"),
                "source": "USGS"
            } for feature in features if feature.get("properties") and feature.get("geometry")]

        return pd.DataFrame(earthquakes)

    except Exception as e:
        st.error(f"Error fetching USGS data: {e}")
        return pd.DataFrame()


# Function to fetch earthquake data from EMSC
def fetch_emsc_data():
    """Fetch earthquake data from EMSC for Italy - last 7 days."""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=7)
    params = {
        "starttime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "endtime":   end_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "minmagnitude": 1.0,
        "maxlatitude": 48.0,
        "minlatitude": 35.0,
        "maxlongitude": 19.0,
        "minlongitude": 6.0,
        "format": "json",
        "limit": 500,
        "orderby": "time"
    }
    try:
        headers = {"User-Agent": "EarthquakeMonitoringApp/1.0"}
        response = requests.get(EMSC_API_URL, params=params, headers=headers, timeout=15)
        if response.status_code != 200:
            return pd.DataFrame()
        data = response.json()
        earthquakes = []
        for event in data.get("features", []):
            props = event.get("properties", {})
            geo   = event.get("geometry", {})
            coords = geo.get("coordinates", [0, 0, 0])
            time_val = props.get("time", "")
            if isinstance(time_val, (int, float)):
                time_str = datetime.fromtimestamp(time_val/1000).strftime("%Y-%m-%dT%H:%M:%S")
            else:
                time_str = str(time_val)[:19]
            earthquakes.append({
                "time":      time_str,
                "magnitude": props.get("mag", 0),
                "depth":     coords[2] if len(coords) > 2 else 0,
                "latitude":  coords[1] if len(coords) > 1 else 0,
                "longitude": coords[0] if len(coords) > 0 else 0,
                "location":  props.get("place", "Unknown"),
                "source":    "EMSC"
            })
        return pd.DataFrame(earthquakes)
    except Exception:
        return pd.DataFrame()


def fetch_gossip_ov_data():
    """
    GOSSIP INGV OV — catalogo sismico rete locale vulcani campani.
    Complementare a INGV FDSN: rileva micro-eventi non nel catalogo nazionale.
    """
    try:
        # Try with verify=True first, fallback to verify=False for INGV cert issues
        try:
            resp = requests.get(
                GOSSIP_OV_URL,
                timeout=8,
                headers={"User-Agent": "EarthquakeMonitoringApp/1.0"},
                verify=True
            )
        except requests.exceptions.SSLError:
            resp = requests.get(  # nosec B501
                GOSSIP_OV_URL,
                timeout=8,
                headers={"User-Agent": "EarthquakeMonitoringApp/1.0"},
                verify=False
            )

        if resp.status_code != 200 or len(resp.content) < 100:
            return pd.DataFrame()

        root = ET.fromstring(resp.text)
        rows = []
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            desc  = (item.findtext("description") or "").strip()
            pub   = (item.findtext("pubDate") or "").strip()

            try:
                from email.utils import parsedate_to_datetime as _p2d
                dt_obj = _p2d(pub)
                dt_str = dt_obj.strftime("%Y-%m-%dT%H:%M:%S")
            except Exception:
                dt_str = pub

            mag_m = re.search(r"magnitudo\s+(?:\w+\s*=\s*)?(\d+\.?\d*)", desc, re.I)
            mag   = float(mag_m.group(1)) if mag_m else 0.0
            lat_m = re.search(r"Lat:\s*([\d.]+)", desc)
            lon_m = re.search(r"Lon:\s*([\d.]+)", desc)
            dep_m = re.search(r"Profondità:\s*([\d.]+)", desc)
            lat = float(lat_m.group(1)) if lat_m else None
            lon = float(lon_m.group(1)) if lon_m else None
            dep = float(dep_m.group(1)) if dep_m else 0.0

            if lat and lon:
                rows.append({
                    "time":      dt_str,
                    "magnitude": mag,
                    "depth":     dep,
                    "latitude":  lat,
                    "longitude": lon,
                    "location":  title.replace("\n", " ").strip(),
                    "source":    "GOSSIP-OV",
                })
        return pd.DataFrame(rows) if rows else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


# Main function to fetch and combine earthquake data from all sources
def fetch_earthquake_data():
    try:
        # Initialize debug info if it doesn't exist
        if 'debug_info' not in st.session_state:
            st.session_state['debug_info'] = {}

        # Set fetch status in debug info
        st.session_state['debug_info']['fetch_start_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Fetch data from all four sources
        ingv_data   = fetch_ingv_data()
        usgs_data   = fetch_usgs_data()
        emsc_data   = fetch_emsc_data()
        gossip_data = fetch_gossip_ov_data()

        # Track data source counts
        st.session_state['debug_info']['ingv_count']   = len(ingv_data)
        st.session_state['debug_info']['usgs_count']   = len(usgs_data)
        st.session_state['debug_info']['emsc_count']   = len(emsc_data)
        st.session_state['debug_info']['gossip_count'] = len(gossip_data)

        # Combine the data (INGV first for dedup priority)
        combined_data = pd.concat([ingv_data, gossip_data, usgs_data, emsc_data], ignore_index=True)
        st.session_state['debug_info']['combined_count'] = len(combined_data)

        if not combined_data.empty:
            # Convert time strings to datetime objects
            combined_data['datetime'] = pd.to_datetime(combined_data['time'], errors='coerce')

            # Count invalid datetimes
            invalid_dates = combined_data['datetime'].isna().sum()
            st.session_state['debug_info']['invalid_dates'] = int(invalid_dates)

            # Filter out rows with invalid datetime
            combined_data = combined_data.dropna(subset=['datetime'])

            # Sort by datetime (most recent first)
            combined_data = combined_data.sort_values(by='datetime', ascending=False)

            # Deduplicate: same event within 60s, 0.3° lat/lon, 0.3 mag — keep INGV > GOSSIP-OV > USGS > EMSC
            _src_order = {"INGV": 0, "GOSSIP-OV": 1, "USGS": 2, "EMSC": 3}
            combined_data['_src_rank'] = combined_data['source'].map(lambda s: _src_order.get(s, 99))
            combined_data = combined_data.sort_values(['_src_rank', 'datetime'], ascending=[True, False])

            deduped = []
            for _, row in combined_data.iterrows():
                duplicate = False
                for kept in deduped:
                    if (abs(row['latitude']  - kept['latitude'])  < 0.3 and
                        abs(row['longitude'] - kept['longitude']) < 0.3 and
                        abs(row['magnitude'] - kept['magnitude']) < 0.3 and
                        abs((row['datetime'] - kept['datetime']).total_seconds()) < 60):
                        duplicate = True
                        break
                if not duplicate:
                    deduped.append(row)

            combined_data = pd.DataFrame(deduped).drop(columns=['_src_rank'], errors='ignore')
            combined_data = combined_data.sort_values(by='datetime', ascending=False)

            # Format the datetime for display
            combined_data['formatted_time'] = combined_data['datetime'].dt.strftime('%d/%m/%Y %H:%M:%S')

        st.session_state['debug_info']['fetch_status'] = 'success'
        return combined_data

    except Exception as e:
        st.error(f"Error processing earthquake data: {str(e)}")
        st.session_state['debug_info']['fetch_status'] = 'error'
        st.session_state['debug_info']['fetch_error'] = str(e)
        return pd.DataFrame()

# Filter earthquakes for specific areas of interest
def filter_area_earthquakes(df, area_name):
    if df is None or df.empty:
        return pd.DataFrame()

    # Define the geographical boundaries for each area
    area_bounds = {
        'vesuvio': {
            'lat_min': 40.70, 'lat_max': 40.95,
            'lon_min': 14.25, 'lon_max': 14.65
        },
        'campi_flegrei': {
            'lat_min': 40.73, 'lat_max': 40.97,
            'lon_min': 13.85, 'lon_max': 14.30
        },
        'ischia': {
            'lat_min': 40.62, 'lat_max': 40.88,
            'lon_min': 13.75, 'lon_max': 14.10
        }
    }

    if area_name in area_bounds:
        bounds = area_bounds[area_name]
        return df[(df['latitude'] >= bounds['lat_min']) & 
                 (df['latitude'] <= bounds['lat_max']) & 
                 (df['longitude'] >= bounds['lon_min']) & 
                 (df['longitude'] <= bounds['lon_max'])]
    else:
        # If no specific area, return all data
        return df

# Get significant earthquakes (magnitude >= 3.0) for notifications
def get_significant_earthquakes(df, min_magnitude=3.0, hours=24):
    if df is None or df.empty:
        return pd.DataFrame()

    # Get earthquakes above the minimum magnitude in the last X hours
    recent_time = datetime.now() - timedelta(hours=hours)

    return df[(df['magnitude'] >= min_magnitude) & 
              (df['datetime'] >= recent_time)]

# Calculate statistics for predictions
def calculate_earthquake_statistics(df):
    if df is None or df.empty:
        return {
            'count': 0,
            'avg_magnitude': 0,
            'max_magnitude': 0,
            'avg_depth': 0,
            'daily_counts': {}
        }

    # Group by days and count earthquakes
    df['date'] = df['datetime'].dt.date
    daily_counts = df.groupby('date').size().to_dict()

    # Format dates as strings for JSON serialization
    daily_counts = {str(k): v for k, v in daily_counts.items()}

    return {
        'count': len(df),
        'avg_magnitude': df['magnitude'].mean(),
        'max_magnitude': df['magnitude'].max(),
        'avg_depth': df['depth'].mean(),
        'daily_counts': daily_counts
    }
