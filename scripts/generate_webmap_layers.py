import geopandas as gpd
import pandas as pd
import glob
import os


ADMIN2_SOURCE_CANDIDATES = ['admin2', 'adm2', 'shapeName', 'name', 'locationName', 'place_name', 'admin_name', 'NOM_DEP', 'nom', 'NAME_3', 'NAME_2', 'NAME_1']

DESIRED_OUTPUT_COLUMNS = [
    'admin2', 'ISO3',
    'adm1', 'min', 'max', 'sum', 'mean', 'num_hh', 'cluster',
    'hh_sum', 'hh_mean', 'hh_max', 'hh_min',
    'geometry' # Always required for GeoDataFrames, ensure it's last
]

# --- Get all GeoJSON file paths ---
files = glob.glob("*.geojson")

if not files:
    print("No GeoJSON files found in the current directory. Please ensure your files are present.")
    exit()

print(f"Found {len(files)} GeoJSON files: {files}")

# --- Load and process each GeoJSON into a list of GeoDataFrames ---
gdf_list = []

for file_path in files:
    try:
        print(f"\nProcessing file: {file_path}")
        gdf = gpd.read_file(file_path)

        # --- Debugging Geometry: Initial check ---
        initial_null_geometries = gdf.geometry.isnull().sum()
        if initial_null_geometries > 0:
            print(f"  Initial check: {initial_null_geometries} features have null geometries in '{os.path.basename(file_path)}'.")

        # Convert to WGS84 (EPSG:4326 / CRS84) for web map compatibility
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            print(f"  Converting CRS from {gdf.crs} to EPSG:4326 (CRS84)...")
            gdf = gdf.to_crs("EPSG:4326")
            null_geometries_after_crs = gdf.geometry.isnull().sum()
            if null_geometries_after_crs > initial_null_geometries:
                print(f"  Warning: {null_geometries_after_crs - initial_null_geometries} new null geometries after CRS conversion.")
        else:
            print("  CRS is already EPSG:4326 (CRS84).")

        # --- Determine the value for the *final* 'admin2' column ---
        gdf['admin2'] = None # Initialize 'admin2' to None or NaN
        found_admin2_source = False
        
        for candidate_col in ADMIN2_SOURCE_CANDIDATES:
            if candidate_col in gdf.columns and not gdf[candidate_col].isnull().all():
                gdf['admin2'] = gdf[candidate_col].astype(str)
                print(f"  Set 'admin2' from '{candidate_col}' column.")
                found_admin2_source = True
                break # Stop searching once a valid source is found.
        
        if not found_admin2_source:
            print(f"  Could not find a suitable source for 'admin2'. 'admin2' set to None for this file's features.")

        gdf['admin2'] = gdf['admin2'].apply(lambda x: str(x) if pd.notna(x) else None)

        # --- Replace values in 'adm1' with "dummy" ---
        if 'adm1' in gdf.columns:
            gdf['adm1'] = 'dummy'
            print("  Replaced all values in 'adm1' column with 'dummy'.")
        else:
            gdf['adm1'] = ['dummy'] * len(gdf)
            print("  'adm1' column not found, created and filled with 'dummy'.")


        # --- Add 'ISO3' to properties ---
        iso3_found = False
        base_filename = os.path.splitext(os.path.basename(file_path))[0]

        if '_' in base_filename:
            possible_iso3 = base_filename.split('_')[0]
            if len(possible_iso3) == 3 and possible_iso3.isalpha() and possible_iso3.isupper():
                gdf['ISO3'] = possible_iso3
                print(f"  Added 'ISO3' property from filename (before underscore): {possible_iso3}")
                iso3_found = True
                
        if not iso3_found:
            if 'iso_a3' in gdf.columns and not gdf['iso_a3'].isnull().all():
                gdf['ISO3'] = gdf['iso_a3'].astype(str)
                print(f"  Added 'ISO3' property from 'iso_a3' column.")
                iso3_found = True
            elif 'ISO_A3' in gdf.columns and not gdf['ISO_A3'].isnull().all():
                gdf['ISO3'] = gdf['ISO_A3'].astype(str)
                print(f"  Added 'ISO3' property from 'ISO_A3' column.")
                iso3_found = True
            elif len(base_filename) == 3 and base_filename.isalpha() and base_filename.isupper():
                gdf['ISO3'] = base_filename
                print(f"  Added 'ISO3' property from full filename: {base_filename}")
                iso3_found = True

        if not iso3_found:
            gdf['ISO3'] = None
            print(f"  Could not derive 'ISO3'. Setting to None.")


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
                print(f"  Warning: Desired output column '{col}' not found in {os.path.basename(file_path)}. It will be null for features from this file.")

        if 'geometry' not in gdf.columns:
            print(f"  Error: No 'geometry' column found in {os.path.basename(file_path)}. Skipping this file.")
            continue
        existing_desired_columns.append('geometry')

        gdf = gdf[existing_desired_columns]
        
        # --- Debugging Geometry: Final check before appending ---
        final_null_geometries = gdf.geometry.isnull().sum()
        if final_null_geometries > 0:
            print(f"  Final check: {final_null_geometries} features still have null geometries in '{os.path.basename(file_path)}' before appending.")
            
        print(f"  Selected columns for output: {existing_desired_columns}")
        
        gdf_list.append(gdf)

    except Exception as e:
        print(f"  Error processing {file_path}: {e}")
        continue

if not gdf_list:
    print("No valid GeoJSON files were processed. Exiting.")
    exit()

# --- Concatenate all GeoDataFrames into one ---
combined_gdf = pd.concat(gdf_list, ignore_index=True)
combined_gdf.crs = "EPSG:4326"

print(f"\nCombined GeoDataFrame created with {len(combined_gdf)} features.")
print("Sample of combined GeoDataFrame head:")
print(combined_gdf.head())
print("\nCombined GeoDataFrame columns:")
print(combined_gdf.columns)
print(f"\nTotal null geometries in combined file: {combined_gdf.geometry.isnull().sum()}")


# --- Save as a new GeoJSON FeatureCollection ---
output_filename = "webmap_layers.geojson"
try:
    combined_gdf.to_file(output_filename, driver="GeoJSON", encoding='utf-8')
    print(f"\nSuccessfully saved combined GeoJSON to '{output_filename}'")
except Exception as e:
    print(f"Error saving combined GeoJSON: {e}")