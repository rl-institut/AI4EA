import os
import re
import ast
import pandas as pd
import geopandas as gpd

LGA_CORRECTION = {
    "Fct": "Federal Capital Territory",  # Nigeria
    "Nasarawa": "Nassarawa",
    "Nasarawa-Eggon": "Nassarawa-Eggon",
    "Markafi": "Makarfi",
    "Ogun waterside": "Ogun Waterside",
    "Ola-oluwa": "Ola-Oluwa",
    "Akwa lbom": "Akwa Ibom",
    "Mai'adua": "Mai'Adua",
    "Matazuu": "Matazu",
    "Tarmua": "Tarmuwa",
    "Ogori/Magongo": "Ogori/Mangongo",
    "Olamabolo": "Olamaboro",
    "Unuimo": "Onu-Imo",
    "Isiukwuato": "Isuikwato",
    "Obi Ngwa": "Obioma Ngwa",
    "Kiri Kasamma": "Kiri-Asamma",
    "Birni Kudu": "Birnin-Kudu",
    "Kaura Namoda": "Kaura-Namoda",
    "Karim-Lamido": "Karim Lamido",
    "Jema'a": "Jemaa",
    "Aiyekire (Gbonyin)": "Aiyekire",
    "Efon": "Efon-Alayee",
    "Barikin Ladi": "Barkin Ladi",
    "Atigbo": "Atisbo",
    "Aiyekire\r\n": "Aiyekire",
    "Aiyedade": "Ayedaade",
    "Esit Eket": "Esit - Eket",
    "Adja-ouèrè": "Adja-Ouere",  # Benin
    "Aguégués": "Aguegues",
    "Akpro-Missérété": "Akpo-Misserete",
    "Aplahoué": "Aplahoue",
    "Athiémé": "Athieme",
    "Bantè": "Bante",
    "Bembèrèkè": "Bembereke",
    "Boukoumbé": "Boukombe",
    "Cobly": "Kobli",
    "Comè": "Come",
    "Covè": "Cove",
    "Dassa": "Dassa-Zoume",
    "Glazoué": "Glazoue",
    "Houéyogbé": "Houeyogbe",
    "Kalalé": "Kalale",
    "Klouekanmè": "Klouekanme",
    "Kouandé": "Kouande",
    "Kpomassè": "Kpomasse",
    "Kérou": "Kerou",
    "Kétou": "Ketou",
    "Matéri": "Materi",
    "Ouaké": "Ouake",
    "Ouèssè": "Ouesse",
    "Pobè": "Pobe",
    "Péhunco": "Pehunco",
    "Péréré": "Perere",
    "Sakété": "Sakete",
    "Savè": "Save",
    "Sinendé": "Sinende",
    "Ségbana": "Segbana",
    "Sémé-Kpodji": "Seme-Kpodji",
    "Tanguiéta": "Tanguieta",
    "Tchaorou": "Tchaourou",
    "Toucoutouna": "Toucountouna",
    "Zè": "Ze",
}


def collect_profiles_path(folder="simulation_data", output_prefix="all_intermediate"):
    pattern = re.compile(output_prefix + r"_(\d+)\.csv")

    # Match and sort files numerically
    matched_files = []
    for f in os.listdir(folder):
        match = pattern.fullmatch(f)
        if match:
            # number = int(match.group(1))
            matched_files.append(f)

    return [os.path.join(folder, f) for f in sorted(matched_files)]


def profiles_indicators(
    profiles_path=None,
    adm1_col="",
    adm2_col="",
    output_fname="demand_profile_stats.csv",
):
    if os.path.exists(output_fname) is False:

        # Read and merge DataFrames on index
        merged_df = []

        for file_path in profiles_path:
            df_temp = pd.read_csv(file_path, index_col=0)  # use index from file
            df = pd.DataFrame()
            df["min"] = df_temp.min(axis=0)
            df["max"] = df_temp.max(axis=0)
            df["sum"] = df_temp.sum(axis=0)
            df["mean"] = df_temp.mean(axis=0)
            merged_df.append(df)

        stats_df = pd.concat(merged_df)

        # Reconstruct the multi-index
        tuples = [ast.literal_eval(t) for t in stats_df.index]
        multi_index = pd.MultiIndex.from_tuples(tuples, names=[adm2_col, adm1_col])
        stats_df.index = multi_index

        stats_df.to_csv(output_fname)

    else:
        print(f"Getting stats from saved file ({output_fname})")
        stats_df = pd.read_csv(output_fname, index_col=[0, 1])

    return stats_df


def profiles_indicators_per_hh(
    stats_df,
    ml_output_path="nga_lga_all_appliance_count.csv",
    adm1_col="",
    adm2_col="",
):
    df_ai = pd.read_csv(ml_output_path)
    df_ai.set_index([adm2_col, adm1_col], inplace=True)
    stats_df = stats_df.join(df_ai.num_hh, how="outer")
    stats_df["hh_sum"] = stats_df["sum"] / stats_df.num_hh
    stats_df["hh_mean"] = stats_df["mean"] / stats_df.num_hh
    stats_df["hh_max"] = stats_df["max"] / stats_df.num_hh
    stats_df["hh_min"] = stats_df["min"] / stats_df.num_hh
    return stats_df


def bind_geometry(
    stats_df, geojson_shapes, adm1_col, adm2_col, adm1_col_geom, adm2_col_geom
):
    gdf = gpd.read_file(geojson_shapes)

    if adm1_col_geom is None:
        col_mapping = {adm2_col_geom: adm2_col}
        col_list = [adm2_col]
    else:
        col_mapping = {adm1_col_geom: adm1_col, adm2_col_geom: adm2_col}
        col_list = [adm1_col, adm2_col]

    gdf.rename(columns=col_mapping, inplace=True)

    for col in col_list:
        gdf[col] = gdf[col].replace(LGA_CORRECTION)

    gdf.set_index(col_list, inplace=True)

    stats_df.rename(index=LGA_CORRECTION, inplace=True)

    if "fid" not in gdf.columns:
        gdf["fid"] = 0

    stats_gdf = gdf[["geometry", "fid"]].join(stats_df, how="outer")
    del stats_gdf["fid"]
    return stats_gdf


def post_process(
    folder="simulation_data",
    output_prefix="all_intermediate",
    adm1_col="",
    adm2_col="",
    output_fname="demand_profile_stats.csv",
    ml_output_path="nga_lga_all_appliance_count.csv",
):
    """

    Parameters:
    -----------
    folder : str
        Directory where the ramp demand profiles are saved.

    output_prefix : str, optional
        Prefix for ramp demand profiles CSV filenames. Files have been saved as:
            - {output_prefix}_avg_{i}.csv (daily profile averaged over one year)
            - {output_prefix}_{i}.csv (yearly profile at minute resolution)

    adm1_col : str, optional
        Name of the column in `path_ml_output` representing the ADM1 administrative unit (e.g., state name).

    adm2_col : str, optional
        Name of the column in `path_ml_output` representing the ADM2 administrative unit (e.g., LGA name).

    output_fname : str, optional
        Directory where output CSV files will be saved. Will be created if it doesn't exist. Default is "output".

    output_fname : str, optional
        Directory where output CSV files will be saved. Will be created if it doesn't exist. Default is "output".

    path_ml_output : str, optional
        File path to the CSV containing machine learning output appliances count.


    """
    profiles_path = collect_profiles_path(folder, output_prefix)
    print("Computing profiles indicators (min, max, mean, aggregation)")
    stats_df = profiles_indicators(profiles_path, adm1_col, adm2_col, output_fname)
    print("Computing profiles indicators per household (min, max, mean, aggregation)")
    stats_df = profiles_indicators_per_hh(stats_df, ml_output_path, adm1_col, adm2_col)
    return stats_df
