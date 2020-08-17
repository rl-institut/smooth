""" DEFINE THE MODEL YOU WANT TO SIMULATE """
import os

# Define where Python should look for csv files
my_path = os.path.join(os.path.dirname(__file__), 'example_timeseries')

""" Create busses """
# create hydrogen bus
busses = ['bel']


""" Define components """
components = list()

components.append({
    'component': 'energy_demand_from_csv',
    'name': 'charge_demand',
    'bus_in': 'bel',
    'csv_filename': 'demand.csv',
    'nominal_value': 1000,  # Umrechnungsfaktor in Wh
    'column_title': 'Charging load',
    'path': my_path
})

components.append({
    'component': 'var_grid',
    'name': 'from_grid',
    'bus_out': 'bel',

    # This example works with grid level 5,
    # while 3 and 4 result in 'termination condition infeasible'
    'grid_level': 5,
    'grid_l3_output_max': 540 * 1e3,  # In W
    'grid_l4_output_max': 1.5 * 1e6,  # In W
    'grid_l5_output_max': 3 * 1e6,  # In W

    'capex_l3': {
        'key': ['poly'],
        'fitting_value': [[120000, 0.02]],
        'dependant_value': ['output_max']},
    'capex_l4': {
        'key': ['poly'],
        'fitting_value': [[500000, 0.02]],
        'dependant_value': ['output_max']},
    'capex_l5': {
        'key': ['poly'],
        'fitting_value': [[1000000, 0.01]],
        'dependant_value': ['output_max']},

    'variable_costs': 0.20 / 1000,  # €/Wh
    'dependency_flow_costs': ('from_grid', 'bel'),
    'life_time': 50,

    'opex': {
        'key': 'spec',
        'fitting_value': 0.01,
        'dependant_value': 'capex'
    }

})

sim_params = {
    'start_date': '1/1/2019',
    'n_intervals': 24,  # wie oft
    'interval_time': 60,  # es wird in Schritten mit dieser MinutenAnzahl gerechnet
    'interest_rate': 0.03,
    'print_progress': True
}

mymodel = {
    'busses': busses,
    'components': components,
    'sim_params': sim_params,
}
