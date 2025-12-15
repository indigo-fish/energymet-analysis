from analysis_code.read_electricity_network import electricity_analysis
from analysis_code.download_era5_data import get_era5
from analysis_code.process_era5_data import era5_processing
import os

for WEATHER_YEAR in [1988, 1998, 2019, 2021]:
    for GRANULARITY in ["1H", "2H", "3H", "4H", "6H"]:
        # Change these lines as needed for different electricity market runs
        RUN_NAME = f"fully_renewable-WY{WEATHER_YEAR}_{GRANULARITY}"

        os.makedirs(f"TEMP_OUTPUTS/{RUN_NAME}", exist_ok=True)
        os.makedirs(f"Figures/{RUN_NAME}", exist_ok=True)

        # Performs full analysis
        electricity_analysis(RUN_NAME, GRANULARITY)
        get_era5(RUN_NAME, WEATHER_YEAR, "era5_data_high-prices")
        era5_processing(RUN_NAME, "era5_data_high-prices")
