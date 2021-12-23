"""
Plots the forecast from NWS.
"""

from typing import Dict, List, Tuple
import requests
import unyt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import pytz
import numpy as np
import textwrap
from scipy.interpolate import interp1d

lat = 42.34013
long = -71.12031
forecast_hours = 36

plt.rcParams["font.family"] = "SF Mono"
plt.rcParams["mathtext.fontset"] = "custom"
COLOR = "white"
plt.rcParams['text.color'] = COLOR
plt.rcParams['axes.labelcolor'] = COLOR
plt.rcParams['xtick.color'] = COLOR
plt.rcParams['ytick.color'] = COLOR

# First, grab the office, etc. data.

url = f"https://api.weather.gov/points/{lat:2.4f},{long:2.4f}"
r = requests.get(url, stream = True)

if r.status_code == 200:
    raw_data = r.json()
    props = raw_data["properties"]

    simple_forecast = props["forecast"]
    detailed_data = props["forecastGridData"]
    location_data = props["relativeLocation"]["properties"]
    city = location_data["city"]
    state = location_data["state"]
    tz = pytz.timezone(props["timeZone"])

    location_name = f"{city}, {state}"
else:
    print("Could not get location information. Check your lat and long, to make sure they are in the NWS service area.")


r = requests.get(simple_forecast, stream = True)

if r.status_code == 200:
    raw_data = r.json()
    today = raw_data["properties"]["periods"][2]
    tomorrow = raw_data["properties"]["periods"][3]
else:
    print("Found location, but could not get the simple forecast.")




def time_data_parser(time_data: List[Dict[str, float]], unit: unyt.unyt_quantity, label: str) -> Tuple[List[datetime.datetime], unyt.unyt_array]:
    times = []
    values = []

    for individual_data in time_data:
        times.append(
            datetime.datetime.strptime(individual_data["validTime"].split("+")[0], "%Y-%m-%dT%H:%M:%S").astimezone(tz=tz)
        )

        values.append(
            individual_data["value"]
        )

    return times, unyt.unyt_array(values, unit, name=label)

r = requests.get(detailed_data, stream = True)

if r.status_code == 200:
    raw_data = r.json()
else:
    print("Found location, but could not get the detailed forecast.")

def data_wrapper(
    name: str,
    unit: unyt.unyt_quantity,
    label: str,
) -> Tuple[List[datetime.datetime], unyt.unyt_array]:
    return time_data_parser(
    time_data=raw_data["properties"][name]["values"],
    unit=unit,
    label=label,
)

T_times, temperatures = data_wrapper("temperature", unyt.C, "Temperature")

H_times, heatIndex = data_wrapper("apparentTemperature", unyt.C, "Feels-Like Temperature")

#print(raw_data["properties"].keys())


# Let's show:
# apparentTemperature
# windSpeed, windGust, windDirection
# probabilityOfPrecipitation
# snowfallAmount, quantitativePrecipitation

fig, ax = plt.subplots(4, 1, sharex=True, figsize=(5, 9), constrained_layout=True)

def wrap_string(
    string,
    n_char=45,
):
    return textwrap.fill(string, n_char)
    #return "\n".join([string[x * n_char: (x+1) * n_char] for x in range((len(string) // n_char) + 1)])

ax[0].axis("off")
ax[0].text(0.5, 0.5,
    f"Forecast for {location_name}\n \n" + 
    wrap_string(f"{today['name']}: {today['detailedForecast']}") + "\n\n" +
    wrap_string(f"{tomorrow['name']}: {tomorrow['detailedForecast']}"),
    ha="center",
    va="center",
    transform=ax[0].transAxes,
    wrap=True,
    color="white",
    fontsize=8
)

with unyt.matplotlib_support:
    ax[1].plot(
        T_times, temperatures, label="True Temperature", color="lightgrey"
    )
    ax[1].plot(
        H_times, heatIndex, label="Feels Like", linestyle="dashed", color="white"
    )
    ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%-I %p\n%a'))
    current_time = datetime.datetime.now(tz=tz)
    ax[1].set_xlim(current_time,current_time + datetime.timedelta(hours=forecast_hours))

ax[1].legend(frameon=False)

# Let's try wind direction

direction_times, directions = data_wrapper("windDirection", "degree", "Wind Direction")
speed_times, wind_speed = data_wrapper("windSpeed", "km/hour", "Wind Speed")
gust_times, wind_gusts = data_wrapper("windGust", "km/hour", "Wind Gust")


wind_speed_interp = interp1d([x.timestamp() for x in speed_times], wind_speed.v, fill_value="extrapolate")

# with unyt.matplotlib_support:
#     # plt.plot(times, wind_speed)
#     plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%-I %p\n%a'))
#     current_time = datetime.datetime.now(tz=tz)
#     plt.xlim(current_time,current_time + datetime.timedelta(hours=forecast_hours))

# plt.tight_layout()
# plt.show()

def find_angle_glyph(angle: unyt.unyt_quantity) -> str:
    angles = unyt.unyt_array([0, 45, 90, 135, 180, 225, 270, 315], "degree")
    index = (np.abs(angle - angles)).argmin()
    styles = ["uparrow", "nearrow", "rightarrow", "searrow", "downarrow", "swarrow", "leftarrow", "nwarrow"]
    return f"$\{styles[index]}$"

with unyt.matplotlib_support:
    for time, direction in zip(direction_times, directions):
        ax[2].scatter(time, wind_speed_interp(time.timestamp()), marker=find_angle_glyph(direction), s=100, color="white")

    ax[2].plot(speed_times, wind_speed, zorder=-5, label="Wind Speed", color="lightgrey")

    ax[2].plot(gust_times, wind_gusts, linestyle="dashed", label="Gust Speed", color="white")
    ax[2].xaxis.set_major_formatter(mdates.DateFormatter('%-I %p\n%a'))


precip_times, probabilities = data_wrapper("probabilityOfPrecipitation", "dimensionless", "Precip Probability")
snow_times, snow_amount = data_wrapper("snowfallAmount", "mm", "Snowfall Amount")
quant_times, quant_amount = data_wrapper('quantitativePrecipitation', "mm", "Precipitation Amount")


with unyt.matplotlib_support:
    ax[3].plot(precip_times, probabilities, zorder=-5, color="white")

    precip_axis = ax[3].twinx()

    precip_axis.bar(quant_times, quant_amount, width=datetime.timedelta(hours=1), alpha=0.5, label="Rain", color="lightgrey")
    precip_axis.bar(snow_times, snow_amount, width=datetime.timedelta(hours=1), alpha=0.5, label="Snow", color="white")

precip_axis.legend(frameon=False)


ax[3].xaxis.set_major_formatter(mdates.DateFormatter('%-I %p\n%a'))
precip_axis.xaxis.set_major_formatter(mdates.DateFormatter('%-I %p\n%a'))

# Finish by styling

for a in list(ax) + [precip_axis]:
    a.spines['top'].set_visible(False)
    a.tick_params(axis="both",direction="in")
    a.spines['bottom'].set_color(COLOR)
    a.spines['top'].set_color(COLOR) 
    a.spines['right'].set_color(COLOR)
    a.spines['left'].set_color(COLOR)

for a in ax:
    a.spines['right'].set_visible(False)

ax[1].set_ylabel("Temperature [C]")
ax[2].set_ylabel("Wind Speed [km/h]")
precip_axis.set_ylabel("Precipitation Amount [mm]")

fig.savefig("current_forecast.png", transparent=True, dpi=144)
