import cdsapi
import pandas as pd
import zipfile
import os

def get_dates(FOLDER):
    # Get list of required dates from a CSV file
    dates_df = pd.read_csv(f'TEMP_OUTPUTS/{FOLDER}/highest_hours.csv', index_col=None, header=[0])
    dates = pd.to_datetime(dates_df['Time'])
    dates = dates.map(lambda d: d.replace(year=2019))
    dates = dates.dt.strftime('%Y-%m-%d').unique().tolist()
    return dates

def download_data(dates, zip_path):

    c = cdsapi.Client()

    c.retrieve(
        'reanalysis-era5-single-levels',
        {
            'product_type': 'reanalysis',
            'variable': ['2m_temperature',
                         "surface_pressure",
                         "100m_u_component_of_wind",
                         "100m_v_component_of_wind",
                         "surface_solar_radiation_downwards"],
            'date': dates,
            'time': ['00:00', '06:00', '12:00', '18:00'],  # all 24 hours
            'area': [49.5, -125, 24, -66.5],  # North, West, South, East (e.g. CONUS)
            'format': 'netcdf',  # request NetCDF file
        },
        zip_path  # output filename
    )

def unzip_data(zip_path, unzip_directory):
    # unzip folder

    # Create the folder if it doesn’t exist
    os.makedirs(unzip_directory, exist_ok=True)

    # Unzip the file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(unzip_directory)

    print(f"Extracted all files to: {unzip_directory}")

def get_era5(FOLDER):
    unzip_directory = f'TEMP_OUTPUTS/{FOLDER}/era5_data_high-prices'
    zip_path = unzip_directory + '.zip'

    dates = get_dates(FOLDER)
    download_data(dates, zip_path)
    unzip_data(zip_path, unzip_directory)