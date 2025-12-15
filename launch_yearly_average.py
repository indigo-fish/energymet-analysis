from analysis_code.download_era5_yearly import get_era5
from analysis_code.process_era5_data import era5_processing_yearly
import os

for WEATHER_YEAR in [1988, 1998, 2019, 2021]:
    # Change these lines as needed for different electricity market runs
    RUN_NAME = f"average-WY{WEATHER_YEAR}"

    os.makedirs(f"TEMP_OUTPUTS/{RUN_NAME}", exist_ok=True)
    os.makedirs(f"Figures/{RUN_NAME}", exist_ok=True)

    # Performs full analysis
    suffix = "era5_data_yearly_average"
    get_era5(RUN_NAME, WEATHER_YEAR, suffix)
    era5_processing_yearly(RUN_NAME, suffix)
