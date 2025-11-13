import cdsapi
import pandas as pd
import zipfile
import os


def get_dates(FOLDER, YEAR):
    # Read the CSV produced by the electricity analysis which lists high-price hours.
    # The CSV is expected at TEMP_OUTPUTS/{FOLDER}/highest_hours.csv and contains a
    # 'Time' column. We convert to datetimes, change the year to the requested YEAR,
    # then return unique date strings in 'YYYY-MM-DD' format for ERA5 requests.
    dates_df = pd.read_csv(
        f"TEMP_OUTPUTS/{FOLDER}/highest_hours.csv", index_col=None, header=[0]
    )
    dates = pd.to_datetime(dates_df["Time"])
    # Replace the year (useful to fetch a particular year's weather on the same month/day)
    dates = dates.map(lambda d: d.replace(year=YEAR))
    dates = dates.dt.strftime("%Y-%m-%d").unique().tolist()
    return dates


def download_data(dates, zip_path):
    # Create a cdsapi.Client and request ERA5 single-level reanalysis for the given dates.
    # The requested variables include 2m temperature, surface pressure, 100m wind components,
    # and surface solar radiation. The output format is NetCDF which the code expects.
    c = cdsapi.Client()

    c.retrieve(
        "reanalysis-era5-single-levels",
        {
            "product_type": "reanalysis",
            # Variables to request from ERA5
            "variable": [
                "2m_temperature",
                "surface_pressure",
                "100m_u_component_of_wind",
                "100m_v_component_of_wind",
                "surface_solar_radiation_downwards",
            ],
            "date": dates,
            # Times chosen per day (here four snapshots: 00, 06, 12, 18 UTC)
            "time": ["00:00", "06:00", "12:00", "18:00"],
            # Area in North, West, South, East (approximate CONUS bounding box)
            "area": [49.5, -125, 24, -66.5],
            "format": "netcdf",  # request NetCDF file
        },
        zip_path,  # output filename for the retrieved archive
    )


def unzip_data(zip_path, unzip_directory):
    # Ensure the target extraction directory exists and extract all files
    # from the downloaded ZIP archive into it.
    os.makedirs(unzip_directory, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(unzip_directory)

    print(f"Extracted all files to: {unzip_directory}")


def get_era5(FOLDER, YEAR):
    # High-level helper that determines the zip output path and triggers
    # the retrieval and extraction for the specified run folder and year.
    unzip_directory = f"TEMP_OUTPUTS/{FOLDER}/era5_data_high-prices"
    zip_path = unzip_directory + ".zip"

    dates = get_dates(FOLDER, YEAR)  # list of YYYY-MM-DD strings
    download_data(dates, zip_path)  # fetch the ERA5 data archive
    unzip_data(zip_path, unzip_directory)  # extract contents for downstream processing
