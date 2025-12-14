import cdsapi
import zipfile
import os


def download_data(year, zip_path):
    # Create a cdsapi.Client and request ERA5 single-level reanalysis for the given dates.
    # The requested variables include 2m temperature, surface pressure, 100m wind components,
    # and surface solar radiation. The output format is NetCDF which the code expects.
    c = cdsapi.Client()

    c.retrieve(
        "reanalysis-era5-single-levels-monthly-means",
        {
            "product_type": ["monthly_averaged_reanalysis_by_hour_of_day"],
            # Variables to request from ERA5
            "variable": [
                "2m_temperature",
                "mean_sea_level_pressure",
                "100m_u_component_of_wind",
                "100m_v_component_of_wind",
                "surface_solar_radiation_downwards",
            ],
            "year": [year],
            "month": [
                "01",
                "02",
                "03",
                "04",
                "05",
                "06",
                "07",
                "08",
                "09",
                "10",
                "11",
                "12",
            ],
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


def get_era5(FOLDER, YEAR, suffix):
    # High-level helper that determines the zip output path and triggers
    # the retrieval and extraction for the specified run folder and year.
    unzip_directory = f"TEMP_OUTPUTS/{FOLDER}/{suffix}"
    zip_path = unzip_directory + ".zip"

    download_data(YEAR, zip_path)  # fetch the ERA5 data archive
    unzip_data(zip_path, unzip_directory)  # extract contents for downstream processing
