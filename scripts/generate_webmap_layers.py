import geopandas as gpd
import pandas as pd
import glob
import os

# Define potential column names for the primary administrative name (which will become 'admin2').
ADMIN2_SOURCE_CANDIDATES = ['admin2', 'adm2', 'shapeName', 'name', 'locationName', 'place_name', 'admin_name', 'NOM_DEP', 'nom', 'NAME_3', 'NAME_2', 'NAME_1']
# Define potential column names for the secondary administrative name (which will become 'admin1').
ADMIN1_SOURCE_CANDIDATES = ['admin1', 'adm1', 'name_1', 'NAME_1', 'ADM1_EN']

# Define the columns (properties) you want to keep in the final combined GeoJSON.
DESIRED_OUTPUT_COLUMNS = [
    'admin1', 'admin2', 'ISO3',
    'min', 'max', 'sum', 'mean', 'num_hh', 'cluster',
    'hh_sum', 'hh_mean', 'hh_max', 'hh_min',
    'geometry' # Always required for GeoDataFrames, ensure it's last
]

# A list of countries for which we want to preserve the original admin data.
SPECIAL_COUNTRIES = ['NGA', 'GHA']

# --- Get all GeoJSON file paths ---
files = glob.glob("*.geojson")

if not files:
    exit()

# --- Load and process each GeoJSON into a list of GeoDataFrames
gdf_list = []

for file_path in files:
    try:
        gdf = gpd.read_file(file_path)

        # Convert to WGS84 (EPSG:4326 / CRS84) for web map compatibility
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs("EPSG:4326")
        
        # --- Filter out null or invalid geometries to prevent issues ---
        gdf = gdf[gdf.geometry.is_valid & ~gdf.geometry.isnull()]

        # --- Derive 'ISO3' first, as it's needed for the condition ---
        iso3_found = False
        base_filename = os.path.splitext(os.path.basename(file_path))[0]
        
        if '_' in base_filename:
            possible_iso3 = base_filename.split('_')[0].upper()
            if len(possible_iso3) == 3 and possible_iso3.isalpha():
                gdf['ISO3'] = possible_iso3
                iso3_found = True
        
        if not iso3_found:
            if 'iso_a3' in gdf.columns and not gdf['iso_a3'].isnull().all():
                gdf['ISO3'] = gdf['iso_a3'].astype(str).str.upper()
                iso3_found = True
            elif 'ISO_A3' in gdf.columns and not gdf['ISO_A3'].isnull().all():
                gdf['ISO3'] = gdf['ISO_A3'].astype(str).str.upper()
                iso3_found = True
            elif len(base_filename) == 3 and base_filename.isalpha() and base_filename.isupper():
                gdf['ISO3'] = base_filename
                iso3_found = True

        if not iso3_found:
            gdf['ISO3'] = None

        # --- Conditional Logic for Admin Layers based on ISO3 ---
        current_iso3 = gdf['ISO3'].iloc[0] if 'ISO3' in gdf.columns and not gdf['ISO3'].empty else None

        if current_iso3 in SPECIAL_COUNTRIES:
            # Initialize final admin columns
            gdf['admin1'] = None
            gdf['admin2'] = None
            
            # Find and set the correct admin1 column
            for candidate_col in ADMIN1_SOURCE_CANDIDATES:
                if candidate_col in gdf.columns and not gdf[candidate_col].isnull().all():
                    gdf['admin1'] = gdf[candidate_col].astype(str)
                    break
            
            # Find and set the correct admin2 column
            for candidate_col in ADMIN2_SOURCE_CANDIDATES:
                if candidate_col in gdf.columns and not gdf[candidate_col].isnull().all():
                    gdf['admin2'] = gdf[candidate_col].astype(str)
                    break

        else: # For all other countries
            # --- Determine the value for the *final* 'admin2' column ---
            gdf['admin2'] = None
            found_admin2_source = False
            
            for candidate_col in ADMIN2_SOURCE_CANDIDATES:
                if candidate_col in gdf.columns and not gdf[candidate_col].isnull().all():
                    gdf['admin2'] = gdf[candidate_col].astype(str)
                    found_admin2_source = True
                    break
            
            if 'admin2' in gdf.columns:
                gdf['admin2'] = gdf['admin2'].apply(lambda x: str(x) if pd.notna(x) else None)
            
            # --- Create 'admin1' with "dummy" value ---
            gdf['admin1'] = 'dummy'
        
        # --- Select only the desired properties ---
        existing_desired_columns = []
        for col in DESIRED_OUTPUT_COLUMNS:
            if col == 'geometry':
                continue
            if col in gdf.columns:
                existing_desired_columns.append(col)
            else:
                gdf[col] = None
                existing_desired_columns.append(col)
        
        if 'geometry' not in gdf.columns:
            continue
        existing_desired_columns.append('geometry')

        gdf = gdf[existing_desired_columns]
        
        gdf_list.append(gdf)

    except Exception as e:
        continue

if not gdf_list:
    exit()

# --- Concatenate all GeoDataFrames into one ---
combined_gdf = pd.concat(gdf_list, ignore_index=True)
combined_gdf.crs = "EPSG:4326"
print(f"\nCombined GeoDataFrame created with {len(combined_gdf)} features.")
print(f"\nTotal null geometries in combined file: {combined_gdf.geometry.isnull().sum()}")

# --- Save as a new GeoJSON FeatureCollection ---
output_filename = "webmap_layers.geojson"
try:
    combined_gdf.to_file(output_filename, driver="GeoJSON", encoding='utf-8')
    print(f"\nSuccessfully saved combined GeoJSON to '{output_filename}'")
except Exception as e:
    print(f"Error saving combined GeoJSON: {e}")
