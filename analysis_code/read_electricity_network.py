import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt
import numpy as np
import pandas as pd
import os
import sys

renewable_map = {
    "CCGT": False,
    "CCGT-95CCS": False,
    "OCGT": False,
    "biomass": True,
    "coal": False,
    "geothermal": True,
    "hydro": True,
    "hydrogen_ct": False,
    "nuclear": False,
    "offwind_floating": True,
    "oil": False,
    "onwind": True,
    "solar": True,
    "waste": False
}

color_map = {
    'CCGT': '#808080',            # mid gray — conventional natural gas
    'CCGT-95CCS': '#a6a6a6',      # lighter gray — gas with CCS
    'OCGT': '#999999',            # similar gray tone — open-cycle gas
    'biomass': '#228B22',         # forest green — organic source
    'coal': '#2F2F2F',            # almost black — coal
    'geothermal': '#D2691E',      # earthy brown — heat from earth
    'hydro': '#1E90FF',           # strong blue — water
    'hydrogen_ct': '#00CED1',     # cyan — hydrogen / clean fuel
    'nuclear': '#FFD700',         # bright yellow — nuclear hazard color
    'offwind_floating': '#4169E1',# royal blue — offshore wind
    'oil': '#4B0082',             # dark indigo — petroleum
    'onwind': '#87CEEB',          # sky blue — onshore wind
    'solar': '#FFA500',           # orange — sunlight
    'waste': '#8B4513'            # brown — waste/organic refuse
}

def read_electricity_network(file_path):
    """Reads the electricity network data from a NetCDF file.

    Args:
        file_path (str): Path to the NetCDF file."""

    ds = xr.open_dataset(file_path)

    # Load the marginal price data
    prices = ds['buses_t_marginal_price']

    # Decode time using snapshots_timestep
    time = xr.cftime_range(
        start='2030-01-01 00:00:00',
        periods=prices.sizes['snapshots'],
        freq='H'
    )
    time = cftime_to_datetime(time)

    # Mean hourly electricity price (averaged across buses)
    mean_hourly_price = prices.mean(dim='buses_t_marginal_price_i')

    # Load the demand data
    demand_p = ds["loads_t_p_set"]
    total_demand = demand_p.sum(dim='loads_t_p_set_i')

    # Load the generation data
    generation_p = ds["generators_t_p"]
    gen_ids = ds["generators_t_p_i"].values.astype(str)
    carriers = ds["generators_carrier"].values.astype(str)

    generation_df = pd.DataFrame(generation_p, index=time, columns=gen_ids)
    gen_carrier_map = dict(zip(gen_ids, carriers))
    generation_by_carrier = generation_df.groupby(gen_carrier_map, axis=1).sum()

    return {"time": time, "mean_hourly_price": mean_hourly_price, "prices": prices, "carriers": carriers, "total_demand": total_demand, "generation_by_carrier": generation_by_carrier}

def cftime_to_datetime(times):
    return [dt.datetime(t.year, t.month, t.day, t.hour) for t in times]

def plot_hourly_price(data, threshold, RUN_NAME):

    time = data["time"]
    all_prices = data["prices"]
    mean_hourly_price = data["mean_hourly_price"]

    fig, ax = plt.subplots()
    plt.plot(time, all_prices, color='lightgray')
    plt.plot([], [], color='lightgray', label='Individual Hourly Bus Prices')
    plt.plot(time, mean_hourly_price, label='Mean Hourly Electricity Price')
    plt.hlines(threshold, time[0], time[-1], color='red', linestyles='dashed', label='Threshold for High Prices')

    # Format the x-axis
    date_format = mdates.DateFormatter('%Y-%m-%d')
    ax.xaxis.set_major_formatter(date_format)
    # Auto-format for better readability
    fig.autofmt_xdate()

    # Format the y-axis
    plt.yscale('log')

    plt.xlabel('Time')
    plt.ylabel('Price (USD)')
    plt.title('Hourly Electricity Prices')
    plt.legend()
    plt.savefig(f'Figures/{RUN_NAME}/hourly_prices.png')
    plt.close()

def plot_generation(data, dates, RUN_NAME):
    time = data["time"]
    generation = data["generation_by_carrier"]

    fig, ax = plt.subplots()
    generation.plot.area(ax=ax, color=[color_map[carrier] for carrier in generation.columns])

    # Format the x-axis
    date_format = mdates.DateFormatter('%Y-%m-%d')
    ax.xaxis.set_major_formatter(date_format)
    # Auto-format for better readability
    fig.autofmt_xdate()

    plt.vlines(dates, 0, max(generation.sum(axis=1)))

    plt.xlabel('Time')
    plt.ylabel('Generation (MW)')
    plt.title('Electricity Generation by Carrier')
    plt.legend(title='Carrier')
    plt.savefig(f'Figures/{RUN_NAME}/generation_by_carrier.png')
    plt.close()

def plot_demand(data, dates, RUN_NAME):
    time = data["time"]
    total_demand = data["total_demand"]
    generation = data["generation_by_carrier"]
    renewable_generation = generation[[col for col in generation.columns if renewable_map[col]]].sum(axis=1)
    demand_net_renewable = total_demand - renewable_generation

    fig, ax = plt.subplots()
    plt.plot(time, total_demand, label='Total Demand', color='blue')
    plt.plot(time, demand_net_renewable, label='Net Renewable', color='red')

    # Format the x-axis
    date_format = mdates.DateFormatter('%Y-%m-%d')
    ax.xaxis.set_major_formatter(date_format)
    # Auto-format for better readability
    fig.autofmt_xdate()

    plt.vlines(dates, 0, max(total_demand))

    plt.xlabel('Time')
    plt.ylabel('Demand (MW)')
    plt.title('Total Electricity Demand Over Time')
    plt.legend()
    plt.savefig(f'Figures/{RUN_NAME}/total_demand.png')
    plt.close()

def find_highest_price_hours(data, n_std=1):
    mean_hourly_price = data["mean_hourly_price"]
    time = data["time"]

    # Get the indices of the top n_std highest prices
    threshold = mean_hourly_price.mean() + n_std * mean_hourly_price.std()
    top_indices = np.where(mean_hourly_price >= threshold)[0]

    highest_hours = [(time[i], mean_hourly_price[i].item()) for i in top_indices]
    return threshold, highest_hours

def electricity_analysis(RUN_NAME):
    FILE = f'DATA/{RUN_NAME}.nc'
    if not os.path.exists(FILE):
        print(f"Error: File '{FILE}' not found.")
        sys.exit(1)

    data = read_electricity_network(FILE)
    threshold, highest_hours = find_highest_price_hours(data)
    df = pd.DataFrame(highest_hours)
    df.columns = ['Time', 'Mean Hourly Price (USD)']

    # Create the folder if it doesn’t exist
    os.makedirs(f'TEMP_OUTPUTS/{RUN_NAME}', exist_ok=True)
    df.to_csv(f'TEMP_OUTPUTS/{RUN_NAME}/highest_hours.csv', index=False)

    dates = df['Time'].dt.strftime('%Y-%m-%d').unique().tolist()

    os.makedirs(f'Figures/{RUN_NAME}', exist_ok=True)
    plot_hourly_price(data, threshold, RUN_NAME)
    plot_generation(data, dates, RUN_NAME)
    plot_demand(data, dates, RUN_NAME)