""" DEFINE THE MODEL YOU WANT TO SIMULATE """
import os

# Define where Python should look for csv files
my_path = os.path.join(os.path.dirname(__file__), 'example_timeseries')

""" Create busses """
# create hydrogen bus
busses = ['bel', 'bh2_1', 'bh2_2', 'bth']


""" Define components """
components = list()

## H2-STORAGE
components.append({
    'component': 'storage_h2',
    'name': 'h2_storage',
    'bus_in': 'bh2_1',
    'bus_out': 'bh2_2',
    'p_min': 2.5,
    'p_max': 40,
    'storage_capacity': 100,  # ToDo add the percantage of the 2.5 bar - should be the usefull storage cap
    'life_time': 20,
    'initial_storage_factor': 0.5,
    # 'slw_factor': 0.5,
    #'vac_in': -100,
    'dependency_flow_costs': ('bh2_l', 'h2_storage'),
    'capex': {
        'key': ['spec', 'poly'],
        'fitting_value': [600, ['cost', 100]],
        'dependant_value': ['storage_capacity', 'p_max']
    },
    'opex': {
        'key': 'spec',
        'fitting_value': 0.01,  # RLI -- NOWs storage is an salt cavern storage so no good
        'dependant_value': 'capex'
    }
})

sim_params = {
    'start_date': '1/1/2019',
    'n_intervals': 10,
    'interval_time': 60,
    'interest_rate': 0.03,
    'print_progress': False,
    'show_debug_flag': False,
}

mymodel = {
    'busses': busses,
    'components': components,
    'sim_params': sim_params,
}
