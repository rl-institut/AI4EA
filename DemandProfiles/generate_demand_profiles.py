import os
import pandas as pd
import geopandas as gpd

from ramp import User, Appliance, UseCase, get_day_type


def prepare_appliance_count(country_iso):
    """The file {country_iso}_appliance_count.geojson is a file containing machine learning output appliances count"""
    gdf = gpd.read_file(f"{country_iso.lower()}_appliance_count.geojson")
    df = gdf[gdf.columns.difference(["geometry"])]
    if "adm1" not in df.columns:
        df["adm1"] = "dummy"
    df.to_csv(f"{country_iso}_appliance_count.csv", index=False)


def process_household_data(
    appliances_df,
    adm1_col,
    adm2_col,
    ramp_template_path="ramp/Household_template.csv",
    save_every=50,
    start_date="2020-01-01",
    end_date="2020-12-31",
    output_prefix="ISO3_all_intermediate",
    output_dir="simulation_data_ISO3",
):
    """
    Processes household data to generate and save daily electricity load profiles
    for each (ADM2, ADM1) administrative unit pair.

    Parameters:
    -----------
    appliance_df : pandas.DataFrame
        A DataFrame containing machine learning output appliances count. It must include at least two columns:
        one representing ADM2 (e.g., 'shapeName') and one for ADM1 (e.g., 'adm1').
        Additionally, it must contain a 'num_hh' column and columns matching the
        unified names defined in the household template CSV.

    adm1_col : str
        Name of the column in `appliances_df` representing the ADM1 administrative unit (e.g., state name).

    adm2_col : str
        Name of the column in `appliances_df` representing the ADM2 administrative unit (e.g., LGA name).

    ramp_template_path : str, optional
        File path to the ramp input household template CSV. Default is "ramp/Household_template.csv".

    save_every : int, optional
        Frequency of intermediate CSV saves, in number of records processed. Each yearly profile weight around 6 MB. Default is 50.

    start_date : str, optional
        Start date for the load profile generation (format: "YYYY-MM-DD"). Default is "2020-01-01".

    end_date : str, optional
        End date for the load profile generation (format: "YYYY-MM-DD"). Default is "2020-12-31".

    output_prefix : str, optional
        Prefix for output CSV filenames. Files will be saved as:
            - {output_prefix}_avg_{i}.csv (daily profile averaged over one year)
            - {output_prefix}_{i}.csv (yearly profile at minute resolution)

    output_dir : str, optional
        Directory where output CSV files will be saved. Will be created if it doesn't exist. Default is "output".

    Raises:
    -------
    ValueError
        If `adm2_col` or `adm1_col` do not exist in `appliances_df`.

    Output:
    -------
    Saves intermediate and final load profile CSV files in the specified directory.
    """

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Check for required columns
    missing_cols = [
        col for col in [adm1_col, adm2_col] if col not in appliances_df.columns
    ]
    if missing_cols:
        raise ValueError(f"Missing column(s) in DataFrame: {', '.join(missing_cols)}")

    # Initialize storage
    series_avg_frame = pd.DataFrame()
    series_frame = pd.DataFrame()

    # Load ramp input template
    df_ramp_template = pd.read_csv(ramp_template_path)

    # Unified names from template
    unified_names = df_ramp_template.unified_names.tolist()

    # Iterate through all rows
    for i, (adm1_name, adm2_name) in enumerate(
        zip(appliances_df[adm1_col], appliances_df[adm2_col])
    ):
        print(f"Processing {i + 1}/{len(appliances_df)}: {adm2_name}, {adm1_name}")

        # Copy template for this ADM2
        df_ramp = df_ramp_template.copy()
        df_ramp["user_name"] = adm2_name

        # Get the appliances numbers
        row_filter = (appliances_df[adm2_col] == adm2_name) & (
            appliances_df[adm1_col] == adm1_name
        )
        numbers = appliances_df.loc[row_filter, unified_names].astype(float)

        if numbers.empty:
            print(f"Warning: No data found for {adm2_name}, {adm1_name}. Skipping.")
            continue

        df_ramp["number"] = numbers.T.squeeze().values

        # UseCase creation from the modified template
        use_case = UseCase(date_start=start_date, date_end=end_date)
        use_case.load_dataframe(df_ramp)
        # Generation of a yearly profile at minute resolution
        profiles_series = use_case.generate_daily_load_profiles()

        # Store the profile into dataframes
        key = (adm2_name, adm1_name)
        # separate in daily profiles (1440 minutes)
        reshaped = profiles_series.reshape(int(len(profiles_series) / 1440), 1440)
        series_avg_frame[key] = reshaped.mean(axis=0)
        series_frame[key] = profiles_series

        # Save results to files
        if i % save_every == 0 and i > 0:
            series_avg_frame.to_csv(
                os.path.join(output_dir, f"{output_prefix}_avg_{i}.csv")
            )
            series_frame.to_csv(os.path.join(output_dir, f"{output_prefix}_{i}.csv"))
            series_avg_frame = pd.DataFrame()
            series_frame = pd.DataFrame()

    # Save the rest of the profiles
    series_avg_frame.to_csv(os.path.join(output_dir, f"{output_prefix}_avg_{i}.csv"))
    series_frame.to_csv(os.path.join(output_dir, f"{output_prefix}_{i}.csv"))


if __name__ == "__main__":
    ISO3 = "NER"
    ml_appliance_count_file = f"{ISO3}_appliance_count.csv"  # This file contains the output of the ML model
    df = pd.read_csv(ml_appliance_count_file)
    if "adm1" not in df.columns:
        df["adm1"] = "dummy"
    process_household_data(
        df,
        adm1_col="adm1",
        adm2_col="shapeName",
        ramp_template_path="ramp_config/Household_template.csv",
        output_prefix=f"{ISO3}_all_intermediate",
        output_dir=f"simulation_data_{ISO3}",
    )
