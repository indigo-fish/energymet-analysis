from analysis_code.read_electricity_network import electricity_analysis
from analysis_code.download_era5_data import get_era5
from analysis_code.process_era5_data import era5_processing

# Change these lines as needed for different electricity market runs
RUN_NAME = "sample_run"
WEATHER_YEAR = 2019

# Performs full analysis
electricity_analysis(RUN_NAME)
get_era5(RUN_NAME, WEATHER_YEAR)
era5_processing(RUN_NAME)
