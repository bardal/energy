# Energy

A few Jupyter notebooks and scripts to help me understand and control home energy use:
- [electricity_usage](electricity_usage.ipynb) to analyse meter readings and show usage by year, month. Meter reading data taken from my Ovo account. Make use of Pandas and Matplotlib to analyse and chart.
- [emoncms_stats](emonpi_stats.ipynb). Load data from emonpi (optical pulse readings) and convert to power to see usage over last few days.
- [weather_forecast](weather_forecast.ipynb). Get forecast from https://openweathermap.org/ and display temperatures.
- [resol_solar_reading.py](resol_solar_reading.py). Read solar heating values over local network from a DeltaSol CS4 connected to a Resol KM2. Barebones implementation of the [VBus](http://danielwippermann.github.io/resol-vbus/#/md/docs/vbus-specification) protocol.
