import os
import pandas as pd


def read_data_file(path, filename, csv_separator, column_title):
    # Function to read the input data files.
    # Parameters:
    #  path = path where the csv file is located [string].
    #  filename = name of csv file [string].
    filepath = os.path.join(path, filename)
    # create specific string for chosen data type
    data = pd.read_csv(filepath, sep=csv_separator, usecols=[column_title])
    return data


def get_date_time_index(start_date, n_intervals, freq):
    # Function defining the parameters for perfect/myopic foresight:
    # Parameters:
    #  start_date: the first evaluated time period
    #  number_of_intervals = number of times the 'for' loop should run [-].
    #  freq = the frequency the time period is evaluated in e.g. 'H' for hours, 'M' for min etc [string].
    date_time_index = pd.date_range(start_date, periods=n_intervals, freq=freq)
    return date_time_index


def interval_time_index(date_time_index, i_interval):
    # Function to divide the set date time index into hourly intervals.
    # Parameters:
    #  date_time_index: chosen date range for the model
    #  this_time_index: the time at each 'for' loop
    this_time_index = date_time_index[i_interval: (i_interval + 1)]
    return this_time_index


def get_sim_time_span(n_interval, freq):
    # Calculate the time span of the simulation.
    # Parameters:
    #  n_interval: number of intervals [-].
    #  freq = the frequency the time period is evaluated in e.g. 'H' for hours, 'M' for min etc [string].

    # Get the time delta.
    time_delta = pd.Timedelta(n_interval, freq)
    # Return the time delta in minutes [min].
    return time_delta.total_seconds() / 60


