""" DEFINE THE MODEL YOU WANT TO SIMULATE """
import os

# Define where Python should look for csv files
my_path = os.path.join(os.path.dirname(__file__), 'example_timeseries')

""" Create busses """
# create hydrogen bus
busses = ['bel', 'bh2_lp', 'bh2_hp', 'bth']


""" Define components """
components = list()
components.append({
    'component': 'electrolyzer',
    'name': 'this_ely',
    'bus_el': 'bel',
    'bus_h2': 'bh2_lp',
    'power_max': 100e3,
    'temp_init': 293.15,
    'life_time': 20,
    'capex': {
        'key': ['free', 'spec'],
        'fitting_value': [[193, -0.366], 'cost'],
        'dependant_value': ['power_max', 'power_max']
    },
    'opex': {
        'key': 'spec',
        'fitting_value': 0.04,
        'dependant_value': 'capex',
    }
})

components.append({
    'component': 'energy_source_from_csv',
    'name': 'solar_output',
    'bus_out': 'bel',
    'csv_filename': 'ts_pv.csv',
    'csv_separator': ';',
    'nominal_value': 1000000/23,
    'column_title': 'PV generation [kWh]',
    'path': my_path
})

components.append({
    'component': 'energy_source_from_csv',
    'name': 'wind_output',
    'bus_out': 'bel',
    'csv_filename': 'ts_wind.csv',
    'nominal_value': 1/4,
    'column_title': 'Power output',
    'path': my_path
})

components.append({
    'component': 'energy_demand_from_csv',
    'name': 'h2_demand',
    'bus_in': 'bh2_hp',
    'csv_filename': 'ts_demand_h2.csv',
    'nominal_value': 1,
    'column_title': 'Hydrogen load',
    'path': my_path
})

components.append({
    'component': 'supply',
    'name': 'from_grid',
    'bus_out': 'bel',
    'output_max': 5000000,
    'variable_costs': 0.00016,
    'fs_component_name': 'h2_storage',
    'fs_attribute_name': 'storage_level',
    'fs_threshold': 200,
    'fs_low_art_cost': -0.001,
    'fs_high_art_cost': 50,
    'dependency_flow_costs': ('from_grid', 'bel'),
})

components.append({
    'component': 'sink',
    'name': 'to_grid',
    'bus_in': 'bel',
    'artificial_costs': 10,
    'dependency_flow_costs': ('bel', 'to_grid'),
})

components.append({
    'component': 'storage_h2',
    'name': 'h2_storage',
    'bus_in': 'bh2_lp',
    'bus_out': 'bh2_lp',
    'p_min': 5,
    'p_max': 450,
    'storage_capacity': 500,
    'life_time': 30,
    'capex': {
        'key': ['poly', 'spec'],
        'fitting_value': [[604.6, 0.5393], 'cost'],
        'dependant_value': ['p_max', 'storage_capacity']
    },
    'opex': {
        'key': 'spec',
        'fitting_value': 0.01,
        'dependant_value': 'capex'
    }
})

components.append({
    'component': 'compressor_h2',
    'name': 'h2_compressor',
    # Busses
    'bus_h2_in': 'bh2_lp',
    'bus_h2_out': 'bh2_hp',
    # Parameters
    'bus_el': 'bel',
    'm_flow_max': 33.6 * 2,
    'life_time': 20,
    # Foreign states
    'fs_component_name': ['h2_storage', None],
    'fs_attribute_name': ['pressure', 700],
    # Financials
    'capex': {
        'key': 'free',
        'fitting_value': [34592, 0.6468],
        'dependant_value': 'm_flow_max'
    },
    'opex': {
        'key': 'spec',
        'fitting_value': 0.04,
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

"""Define any external components that should not be considered in the simulation/optimization"""
external_components = list()

external_components.append({
    'external_component': 'h2_dispenser',
    'name': 'test',
    'life_time': 20,
    # Financials
    'capex': {
        'key': 'spec',
        'fitting_value': 107000,
        'dependant_value': 'number_of_units'
    },
    'opex': {
        'key': 'spec',
        'fitting_value': 0.05,
        'dependant_value': 'capex'
    },
    'csv_filename': 'ts_demand_h2.csv',
    'nominal_value': 1,
    'column_title': 'Hydrogen load',
    'path': my_path
})


sim_params = {
    'start_date': '1/1/2019',
    'n_intervals': 10,
    'interval_time': 60,
    'interest_rate': 0.03,
    'print_progress': True
}


mymodel = {
    'busses': busses,
    'components': components,
    'sim_params': sim_params,
    'external_components': external_components
}
