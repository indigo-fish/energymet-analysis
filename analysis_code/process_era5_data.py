import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt


def load_data(FOLDER):
    # Compose file paths for the instant vs accumulated streams produced by the ERA5 download.
    FILE1 = f"TEMP_OUTPUTS/{FOLDER}/era5_data_high-prices/data_stream-oper_stepType-instant.nc"
    data1 = xr.open_dataset(FILE1, engine="netcdf4")

    FILE2 = f"TEMP_OUTPUTS/{FOLDER}/era5_data_high-prices/data_stream-oper_stepType-accum.nc"
    data2 = xr.open_dataset(FILE2, engine="netcdf4")

    # Merge datasets so we have all required variables in a single xarray Dataset.
    data = xr.merge([data1, data2])

    # Convert ERA5 variables to more convenient units:
    # - t2m: Kelvin -> Celsius
    # - sp: Pascals -> hectopascals (hPa)
    # - u100, v100: components used to compute wind speed (m s^-1)
    # - ssrd: surface solar radiation downwards given as J m^-2 over the period;
    #   dividing by 3600 approximates an hourly average in W m^-2 when data are hourly accumulations.
    temperature_2m = data["t2m"] - 273.15  # from Kelvin to C
    surface_pressure = data["sp"] / 100  # from Pa to hPa
    u_100m = data["u100"]
    v_100m = data["v100"]
    windspeed_100m = (u_100m**2 + v_100m**2) ** 0.5  # m s^-1
    surface_radiation = data["ssrd"] / 3600  # W m^-2 instead of J m^-2 over 1 hour

    # Save commonly used coordinate variables for later plotting
    time = data["valid_time"]
    lat = data["latitude"]
    lon = data["longitude"]

    # Map variable display names to computed DataArray objects, units and colormaps
    label_map = {
        "2m Temperature": temperature_2m,
        "Surface Pressure": surface_pressure,
        "100m Wind Speed": windspeed_100m,
        "Global Horizontal Irradiance": surface_radiation,
    }
    unit_map = {
        "2m Temperature": "$^o$C",
        "Surface Pressure": "hPa",
        "100m Wind Speed": "m s$^{-1}$",
        "Global Horizontal Irradiance": "W m$^{-2}$",
    }
    color_map = {
        "2m Temperature": "bwr",
        "Surface Pressure": "cividis",
        "100m Wind Speed": "viridis",
        "Global Horizontal Irradiance": "magma",
    }

    return label_map, unit_map, color_map, time, lat, lon


def plot_dataset(variable, ds, unit_map, color_map, FOLDER):
    # Take a time-mean across the 'valid_time' dimension so the plot shows
    # an aggregated snapshot (average over the requested times).
    dataset = ds.mean(dim="valid_time")

    # Create a cartopy map axes using PlateCarree projection (simple lat/lon)
    plt.figure(figsize=(12, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())  # The projection for the plot

    # Use xarray/matplotlib to plot the gridded dataset onto the map.
    # transform=PlateCarree tells cartopy the data's coordinate system is regular lon/lat.
    dataset.plot(
        ax=ax,
        transform=ccrs.PlateCarree(),
        levels=10,  # number of contour levels / filled intervals
        cmap=color_map[variable],
        cbar_kwargs={"label": unit_map[variable]},
    )

    # Add map context: coastlines, country borders and US state borders
    ax.coastlines()
    ax.add_feature(cfeature.BORDERS, linewidth=1)
    ax.add_feature(cfeature.STATES, linewidth=0.5)

    # Add gridlines and control which edges show the lat/lon labels
    gl = ax.gridlines(
        draw_labels=True, linewidth=0.5, color="gray", alpha=0.5, linestyle="--"
    )
    gl.top_labels = False
    gl.right_labels = False

    # Adjust label appearance for clarity
    gl.xlabel_style = {"size": 10, "color": "gray"}
    gl.ylabel_style = {"size": 10, "color": "gray"}

    # Finalize and write the figure to the Figures folder for the run
    plt.title(f"{variable} ({unit_map[variable]})")
    plt.savefig(f"Figures/{FOLDER}/{variable}.png", bbox_inches="tight")


def era5_processing(FOLDER):
    # Load processed DataArrays and metadata then loop over each variable to plot.
    label_map, unit_map, color_map, time, lat, lon = load_data(FOLDER)
    for variable, ds in label_map.items():
        plot_dataset(variable, ds, unit_map, color_map, FOLDER)
