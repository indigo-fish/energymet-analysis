import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt
import numpy as np
import pandas as pd
import os
import sys

# Sort which technologies to include in the "demand-net-renewables" calculation
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
    "offwind": True,
    "offwind_floating": True,
    "oil": False,
    "onwind": True,
    "solar": True,
    "waste": False,
}

# Hardcode unique colours for plotting generation from each technology
color_map = {
    "CCGT": "#808080",  # mid gray — conventional natural gas
    "CCGT-95CCS": "#a6a6a6",  # lighter gray — gas with CCS
    "OCGT": "#999999",  # similar gray tone — open-cycle gas
    "biomass": "#228B22",  # forest green — organic source
    "coal": "#2F2F2F",  # almost black — coal
    "geothermal": "#D2691E",  # earthy brown — heat from earth
    "hydro": "#1E90FF",  # strong blue — water
    "hydrogen_ct": "#00CED1",  # cyan — hydrogen / clean fuel
    "nuclear": "#FFD700",  # bright yellow — nuclear hazard color
    "offwind_floating": "#A569E1",  # purple — floating offshore wind
    "offwind": "#4169E1",  # royal blue — offshore wind
    "oil": "#4B0082",  # dark indigo — petroleum
    "onwind": "#87CEEB",  # sky blue — onshore wind
    "solar": "#FFA500",  # orange — sunlight
    "waste": "#8B4513",  # brown — waste/organic refuse
}


def read_electricity_network(file_path, frequency):
    """Reads the electricity network data from a NetCDF file.

    :param file_path: Path to the NetCDF file.
    :return: dict with keys: time, mean_hourly_price, prices, carriers,
             total_demand, generation_by_carrier
    """
    # Open the dataset with xarray (lazy loading by default)
    ds = xr.open_dataset(file_path)

    # Load the marginal price data (time x buses)
    prices = ds["buses_t_marginal_price"]

    # Build a time index for the snapshots. The original dataset uses
    # a regular hourly frequency, so construct a cftime_range and convert.
    time = xr.cftime_range(
        start="2050-01-01 00:00:00", periods=prices.sizes["snapshots"], freq=frequency
    )
    # Convert cftime objects to native Python datetimes for plotting and pandas usage
    time = cftime_to_datetime(time)

    # Aggregate to get mean hourly price across all buses
    mean_hourly_price = prices.mean(dim="buses_t_marginal_price_i")

    # Load total demand: loads_t_p_set is per-load; sum across load indices to get system demand
    demand_p = ds["loads_t_p_set"]
    total_demand = demand_p.sum(dim="loads_t_p_set_i")

    # Load generation time series per generator
    generation_p = ds["generators_t_p"]
    gen_ids = ds["generators_t_p_i"].values.astype(str)  # generator identifiers
    carriers = ds["generators_carrier"].values.astype(str)  # carrier type per generator

    # Build a pandas DataFrame indexed by time with generator columns
    generation_df = pd.DataFrame(generation_p, index=time, columns=gen_ids)

    # Create a mapping from generator id -> carrier and group by carrier to get carrier-level generation
    gen_carrier_map = dict(zip(gen_ids, carriers))
    generation_by_carrier = generation_df.groupby(gen_carrier_map, axis=1).sum()

    # Return a compact dictionary for downstream plotting/analysis
    return {
        "time": time,
        "mean_hourly_price": mean_hourly_price,
        "prices": prices,
        "carriers": carriers,
        "total_demand": total_demand,
        "generation_by_carrier": generation_by_carrier,
    }


def cftime_to_datetime(times):
    """
    Convert a sequence of cftime objects to Python datetime objects.
    This helps with matplotlib and pandas which expect standard datetime.
    :param times: iterable of cftime objects
    :return: list of datetime.datetime objects
    """
    # Use list comprehension for clarity and explicit field extraction
    return [dt.datetime(t.year, t.month, t.day, t.hour) for t in times]


def plot_hourly_price(data, threshold, RUN_NAME):
    """
    Plot individual bus prices (light gray), mean hourly price (line),
    and a horizontal threshold line marking high-price events.
    """
    time = data["time"]
    all_prices = data["prices"]
    mean_hourly_price = data["mean_hourly_price"]

    fig, ax = plt.subplots()
    # Plot each bus's price time series in the background (light gray)
    plt.plot(time, all_prices, color="lightgray")
    plt.plot(
        [], [], color="lightgray", label="Individual Hourly Bus Prices"
    )  # legend entry
    # Plot the mean hourly price as the main line
    plt.plot(time, mean_hourly_price, label="Mean Hourly Electricity Price")
    # Draw a horizontal dashed line at the threshold for high prices
    plt.hlines(
        threshold,
        time[0],
        time[-1],
        color="red",
        linestyles="dashed",
        label="Threshold for High Prices",
    )

    # ---- Set x-axis limits ----
    ax.set_xlim(pd.Timestamp("2050-01-01"), pd.Timestamp("2051-01-01"))

    # Format the x-axis to show dates clearly
    date_format = mdates.DateFormatter("%Y-%m-%d")
    ax.xaxis.set_major_formatter(date_format)
    fig.autofmt_xdate()  # rotate and align date labels

    # Use log scale if prices vary over orders of magnitude
    plt.yscale("log")

    # Labels, title and legend
    plt.xlabel("Time")
    plt.ylabel("Price (USD)")
    plt.title("Hourly Electricity Prices")
    plt.legend()
    # Save the figure to the run-specific Figures folder
    plt.savefig(f"Figures/{RUN_NAME}/hourly_prices.png")
    plt.close()


def plot_generation(data, dates, RUN_NAME):
    """
    Stacked area plot of generation by carrier. Vertical lines mark dates
    that contain high-price events.
    """
    generation = data["generation_by_carrier"]

    fig, ax = plt.subplots()
    # stackplot expects columns ordered; transpose to pass series per carrier
    ax.stackplot(
        generation.index,
        generation.T,
        labels=generation.columns,
        colors=[color_map[carrier] for carrier in generation.columns],
    )

    # ---- Set x-axis limits ----
    ax.set_xlim(pd.Timestamp("2050-01-01"), pd.Timestamp("2051-01-01"))

    # Format x-axis for readability
    date_format = mdates.DateFormatter("%Y-%m-%d")
    ax.xaxis.set_major_formatter(date_format)
    fig.autofmt_xdate()

    # Draw vertical lines at dates with high-price events (spanning from 0 to max generation)
    plt.vlines(
        dates,
        0,
        max(generation.sum(axis=1)),
        color="black",
        linestyle="dashed",
        label="High Prices",
    )

    plt.xlabel("Time")
    plt.ylabel("Generation (MW)")
    plt.title("Electricity Generation by Carrier")
    plt.legend(title="Carrier")
    plt.savefig(f"Figures/{RUN_NAME}/generation_by_carrier.png")
    plt.close()


def plot_demand(data, dates, RUN_NAME):
    """
    Plot total system demand and demand net renewables (total - selected renewables).
    Vertical lines indicate dates with high-price events.
    """
    time = data["time"]
    total_demand = data["total_demand"]
    generation = data["generation_by_carrier"]

    # Sum generation across carriers that are flagged as renewable in renewable_map
    renewable_generation = generation[
        [col for col in generation.columns if renewable_map[col]]
    ].sum(axis=1)
    # Compute demand net of renewable generation for comparison
    demand_net_renewable = total_demand - renewable_generation

    fig, ax = plt.subplots()
    plt.plot(time, total_demand, label="Total Demand", color="blue")
    plt.plot(time, demand_net_renewable, label="Net Renewable", color="red")

    # ---- Set x-axis limits ----
    ax.set_xlim(pd.Timestamp("2050-01-01"), pd.Timestamp("2051-01-01"))

    # Format dates on x-axis
    date_format = mdates.DateFormatter("%Y-%m-%d")
    ax.xaxis.set_major_formatter(date_format)
    fig.autofmt_xdate()

    # Mark high-price dates visually
    plt.vlines(
        dates,
        0,
        max(total_demand),
        color="black",
        linestyle="dashed",
        label="High Prices",
    )

    plt.xlabel("Time")
    plt.ylabel("Demand (MW)")
    plt.title("Total Electricity Demand Over Time")
    plt.legend()
    plt.savefig(f"Figures/{RUN_NAME}/total_demand.png")
    plt.close()


def find_highest_price_hours(data, n_std=1):
    """
    Identify hours where the mean hourly price exceeds mean + n_std * std.
    Returns the threshold value and a list of (time, price) tuples for those hours.
    """
    mean_hourly_price = data["mean_hourly_price"]
    time = data["time"]

    # Compute threshold as mean plus n_std times standard deviation
    threshold = mean_hourly_price.mean() + n_std * mean_hourly_price.std()
    # Find indices where the mean hourly price meets/exceeds the threshold
    top_indices = np.where(mean_hourly_price >= threshold)[0]

    # Pair timestamps with numeric values (convert xarray scalar to native Python float)
    highest_hours = [(time[i], mean_hourly_price[i].item()) for i in top_indices]
    return threshold, highest_hours


def electricity_analysis(RUN_NAME, frequency):
    """
    Top-level entry point for the electricity analysis.
    Loads the specified NetCDF run, finds high-price hours, and
    writes outputs and figures to disk.
    """
    FILE = f"DATA/{RUN_NAME}.nc"
    # Ensure the expected file exists, otherwise exit with an error message
    if not os.path.exists(FILE):
        print(f"Error: File '{FILE}' not found.")
        sys.exit(1)

    # Read and preprocess the network data
    data = read_electricity_network(FILE, frequency)
    # Identify the threshold and the hours that exceed it
    threshold, highest_hours = find_highest_price_hours(data)
    df = pd.DataFrame(highest_hours)
    df.columns = ["Time", "Mean Hourly Price (USD)"]

    # Ensure output directories exist and persist the list of high-price hours
    df.to_csv(f"TEMP_OUTPUTS/{RUN_NAME}/highest_hours.csv", index=False)

    # Extract unique dates that contain high-price hours for plotting vertical lines
    dates = df["Time"].dt.strftime("%Y-%m-%d").unique().tolist()

    # Ensure figure directory exists and create plots
    plot_hourly_price(data, threshold, RUN_NAME)
    plot_generation(data, dates, RUN_NAME)
    plot_demand(data, dates, RUN_NAME)
