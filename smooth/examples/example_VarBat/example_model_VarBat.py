""" DEFINE THE MODEL YOU WANT TO SIMULATE """
import os

# Define where Python should look for csv files
my_path = os.path.join(os.path.dirname(__file__), 'timeseries')

""" Create busses """
# create elektric bus
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
    'component': 'supply',
    'name': 'from_grid',
    'bus_out': 'bel',
    'output_max': 2.5 * 1e6,
    'variable_costs': 0.20 / 1000,  # €/Wh
    'dependency_flow_costs': ('from_grid', 'bel'),
    'life_time': 50,
})

components.append({
    'component': 'var_battery',
    'name': 'Li_battery',
    'bus_in_and_out': 'bel',

    'battery_type': 2,

    # Battery type 1: Li_battery 1 - 50 kWh
    'battery_capacity_bt1': 50 * 1e3,
    # Battery type 2: Li_battery 50 - 1000 kWh
    'battery_capacity_bt2': 1000000,
    # Battery type 3: Li_battery > 1 MWh
    'battery_capacity_bt3': 2 * 1e6,

    # Capex for each battery type
    'capex_bt1': {
        'key': ['poly', 'spec'],
        'fitting_value': [[0, 2109.62368 / 1e3, -147.52325 / 1e6, 6.97016 / 1e9, -0.13996 / 1e12,
                           0.00102 / 1e15],
                          'cost'],
        'dependant_value': ['battery_capacity', 'c_rate_insig_cost']},
    'capex_bt2': {
        'key': ['poly', 'spec'],
        'fitting_value': [[0, 1000.2 / 1e3, -0.4983 / 1e6], 'cost'],
        'dependant_value': ['battery_capacity', 'c_rate_insig_cost']},
    'capex_bt3': {
        'key': ['poly', 'spec'],
        'fitting_value': [[0.353, 0.149], 'cost'],  # für 2020
        'dependant_value': ['c_rate', 'battery_capacity']},

    'soc_init': 1,
    'c_rate': 0.3,
    # 'c_rate': 1,
    'life_time': 20,
    'dod': 0.2,
    'loss_rate': 0.001,  # [(%*100)/day]
    'vac_in': -10,
    'vac_out': 0.01,
    'opex': {
        'key': 'spec',
        'fitting_value': 0.02,
        'dependant_value': 'capex'
    }
})

sim_params = {
    'start_date': '1/1/2019',
    'n_intervals': 24,  # wie oft
    'interval_time': 60,  # es wird in Schritten mit dieser Minuten Anzahl gerechnet
    'interest_rate': 0.03,
    'print_progress': True,
    'show_debug_flag': False,
}

mymodel = {
    'busses': busses,
    'components': components,
    'sim_params': sim_params,
}
