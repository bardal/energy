# Energy

A collection of Jupyter notebooks and a small Python script for analysing and monitoring home energy data.

## Contents

- **electricity_usage.ipynb** – Parses `meter_readings.txt` from an energy provider and charts electricity use by year and month.
- **emonpi_stats.ipynb** – Loads optical pulse data from an emonPi logger and converts it into power readings for short‑term usage graphs.
- **weather_forecast.ipynb** – Fetches temperature forecasts from [OpenWeatherMap](https://openweathermap.org) and visualises them with matplotlib and seaborn.
- **resol_solar_reading.py** – Connects to a Resol KM2/DeltaSol CS4 controller and prints solar heating values using a minimal implementation of the VBus protocol.

## Requirements

The notebooks expect Python 3 with the standard data-science stack installed:

```
pandas
numpy
matplotlib
seaborn
dateparser
requests
```

Any of the notebooks can be opened in JupyterLab or another notebook environment and run cell by cell. `meter_readings.txt` provides example electricity readings used by `electricity_usage.ipynb`.

### Solar Reading Script

The `resol_solar_reading.py` script is standalone and relies only on the Python standard library. Invoke it with the IP address and password of your KM2 device:

```bash
python resol_solar_reading.py -v 192.168.1.100 yourpassword
```

The optional `-v` flag prints each step of the VBus communication while the script waits for data frames.

## Data

`meter_readings.txt` contains chronological readings in the following form:

```
21 Jul 2021You gave129990
06 Jul 2021You gave129062
```

These values are parsed into a DataFrame for further analysis and visualisation.

## License

This repository does not specify a licence. Use at your own discretion.

