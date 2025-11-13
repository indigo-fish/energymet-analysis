from analysis_code.read_electricity_network import electricity_analysis
from analysis_code.download_era5_data import get_era5
from analysis_code.process_era5_data import era5_processing

RUN_NAME = 'sample_run'

electricity_analysis(RUN_NAME)
get_era5(RUN_NAME)
era5_processing(RUN_NAME)