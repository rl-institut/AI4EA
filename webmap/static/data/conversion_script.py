import os
import re
import pandas as pd
country_iso = "TGO"

def collect_profiles_path(folder, output_prefix="all_intermediate_avg"):
    pattern = re.compile(output_prefix + r"_(\d+)\.csv")

    # Match and sort files numerically
    matched_files = []
    for f in os.listdir(folder):
        match = pattern.fullmatch(f)
        if match:
            # number = int(match.group(1))
            matched_files.append(f)

    return [os.path.join(folder, f) for f in sorted(matched_files)]


if __name__ == "__main__":
    if country_iso == "":
        print("! --- Please provide a country iso3 --- !")
    else:
        # Read and merge DataFrames on index
        merged_df = pd.DataFrame()
        # TODO HERE update the name of the folder where your "{country_iso}_all_intermediate_avg" files are
        folder_path = f"simulation_data_{country_iso}"

        sorted_files = collect_profiles_path(folder_path, output_prefix=f"{country_iso}_all_intermediate_avg")
        print(sorted_files)
        for file_path in sorted_files:
            df = pd.read_csv(file_path, index_col=0)  # use index from file
            if merged_df.empty:
                merged_df = df
            else:
                merged_df = merged_df.join(df, how='outer')  # or 'inner' if strict alignment needed

        # Full year example: 2024 (leap year)
        start = '2024-01-01 00:00'
        end = '2024-01-01 23:59'

        # Create datetime index at 1-minute frequency
        time = pd.date_range(start=start, end=end, freq='min')

        # Turn the timeseries into
        merged_df.index = time
        ds = merged_df.stack().reset_index()
        ds.columns = ['time', 'location', 'value']
        xr_ds = ds.set_index(['location', 'time']).to_xarray()
        print(f"Will occupy {xr_ds.nbytes / 1e6} MB")
        xr_ds.to_netcdf(f"{country_iso}_timeseries_daily_avg.nc")
