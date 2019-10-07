import os
import pandas as pd

###########################################################################################

# function to read the input data files:
## path = path where the csv file is lcoated e.g.
# r'C:\Users\ciara.dunks\PycharmProjects\oemof practice\step by step simulation\general_optimization'
## filename = name of csv file e.g. 'e126.power_output.csv'

def read_data_file(path, filename, csv_separator, column_title):
    filepath = os.path.join(path, filename)
    # create specific string for chosen data type
    data = pd.read_csv(filepath, sep=csv_separator, usecols=[column_title])
    return data

##########################################################################################

# function defining the parameters for perfect/myopic foresight:
## start_date = the first evaluated time period
## number_of_intervals = number of times the 'for' loop should run
## freq = the frequency the time period is evaluated in e.g. 'H' for hours, 'M' for min etc.

def set_date_time_index(start_date, n_intervals, freq):
    date_time_index = pd.date_range(start_date, periods=n_intervals + 1,
                                    freq = freq)
    return date_time_index

########################################################################################

# function to divide the set date time index into hourly intervals:
## date_time_index = chosen date range for the model
## this_time_index = the time at each 'for' loop

def interval_time_index(date_time_index, i_interval):
    # date_time_index = sim_params['date_time_index']
    # i_interval = sim_params['i_interval']
    this_time_index = date_time_index[i_interval: (i_interval + 1)]
    return this_time_index

