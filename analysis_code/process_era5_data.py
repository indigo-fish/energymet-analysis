import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt

def load_data(FOLDER):

    FILE1 = f"TEMP_OUTPUTS/{FOLDER}/era5_data_high-prices/data_stream-oper_stepType-instant.nc"

    data1 = xr.open_dataset(FILE1, engine='netcdf4')

    FILE2 = f"TEMP_OUTPUTS/{FOLDER}/era5_data_high-prices/data_stream-oper_stepType-accum.nc"

    data2 = xr.open_dataset(FILE2, engine='netcdf4')

    data = xr.merge([data1, data2])

    temperature_2m = data['t2m'] - 273.15 # from Kelvin to C
    surface_pressure = data['sp'] / 100 # from Pa to hPa
    u_100m = data['u100']
    v_100m = data['v100']
    windspeed_100m = (u_100m ** 2 + v_100m ** 2) ** 0.5 # m s^-1
    surface_radiation = data['ssrd'] / 3600 # W m^-2 instead of J m^-2 over 1 hour

    time = data['valid_time']
    lat = data['latitude']
    lon = data['longitude']

    label_map = {"2m Temperature": temperature_2m, "Surface Pressure": surface_pressure, "100m Wind Speed": windspeed_100m, "Global Horizontal Irradiance": surface_radiation}
    unit_map = {"2m Temperature": "$^o$C", "Surface Pressure": "hPa", "100m Wind Speed": "m s$^{-1}$", "Global Horizontal Irradiance": "W m$^{-2}$"}
    color_map = {"2m Temperature": "bwr", "Surface Pressure": "cividis", "100m Wind Speed": "viridis", "Global Horizontal Irradiance": "magma"}

    return label_map, unit_map, color_map, time, lat, lon

def plot_dataset(variable, ds, unit_map, color_map, FOLDER):
    dataset = ds.mean(dim='valid_time')

    # Create the plot
    fig = plt.figure(figsize=(12, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())  # You can change projection

    # Plot data (using xarray's built-in .plot)
    p = dataset.plot(
        ax=ax,
        transform=ccrs.PlateCarree(),  # The coordinate system of the data
        levels=10,
        cmap=color_map[variable],
        cbar_kwargs={'label': unit_map[variable]},
    )

    # Add coastlines and other features
    ax.coastlines()
    ax.add_feature(cfeature.BORDERS, linewidth=1)  # Country borders
    ax.add_feature(cfeature.STATES, linewidth=0.5)  # US state borders

    # Add gridlines with labels
    gl = ax.gridlines(
        draw_labels=True,  # Show latitude/longitude labels
        linewidth=0.5, color='gray',
        alpha=0.5, linestyle='--'
    )

    # Control which sides show labels
    gl.top_labels = False
    gl.right_labels = False

    # Optionally format tick labels
    gl.xlabel_style = {'size': 10, 'color': 'gray'}
    gl.ylabel_style = {'size': 10, 'color': 'gray'}

    plt.title(f"{variable} ({unit_map[variable]})")
    plt.savefig(f'Figures/{FOLDER}/{variable}.png', bbox_inches='tight')

def era5_processing(FOLDER):
    label_map, unit_map, color_map, time, lat, lon = load_data(FOLDER)
    for variable, ds in label_map.items():
        plot_dataset(variable, ds, unit_map, color_map, FOLDER)