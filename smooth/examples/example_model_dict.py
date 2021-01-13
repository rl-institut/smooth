"""
This example demonstrates how the components can be created in a dictionary
instead of a list, which has advantages over the list form such as the
inherent uniqueness of component names as well as easier access to components
by name. This is particularly useful for large systems with many components.

An example of a component created as a dictionary entry is displayed below:

.. code:: bash

    components = {
        "this_ely": {
            "component": "electrolyzer",
            "bus_el": "bel",
            "bus_h2": "bh2_lp",
            "power_max": 100000.0,
            "temp_init": 293.15,
            "life_time": 20,
            "capex": {
                "key": [
                    "free",
                    "spec"
                ],
                "fitting_value": [
                    [
                        193,
                        -0.366
                    ],
                    "cost"
                ],
                "dependant_value": [
                    "power_max",
                    "power_max"
                ]
            },
            "opex": {
                "key": "spec",
                "fitting_value": 0.04,
                "dependant_value": "capex"
            }
    }

"""
import os

# Define where Python should look for csv files
my_path = os.path.join(os.path.dirname(__file__), 'example_timeseries')

# Create busses
busses = ['bel', 'bh2_lp', 'bh2_hp']


# Define components
components = {
    "this_ely": {
        "component": "electrolyzer",
        "bus_el": "bel",
        "bus_h2": "bh2_lp",
        "power_max": 100000.0,
        "temp_init": 293.15,
        "life_time": 20,
        "capex": {
            "key": [
                "free",
                "spec"
            ],
            "fitting_value": [
                [
                    193,
                    -0.366
                ],
                "cost"
            ],
            "dependant_value": [
                "power_max",
                "power_max"
            ]
        },
        "opex": {
            "key": "spec",
            "fitting_value": 0.04,
            "dependant_value": "capex"
        }
    },
    "pv_output": {
        "component": "energy_source_from_csv",
        "bus_out": "bel",
        "csv_filename": "ts_pv.csv",
        "csv_separator": ";",
        "nominal_value": 43478.260869565216,
        "column_title": "PV generation [kWh]",
        "path": my_path
    },
    "wind_output": {
        "component": "energy_source_from_csv",
        "bus_out": "bel",
        "csv_filename": "ts_wind.csv",
        "csv_separator": ";",
        "nominal_value": 0.25,
        "column_title": "Power output",
        "path": my_path
    },
    "h2_demand": {
        "component": "energy_demand_from_csv",
        "bus_in": "bh2_hp",
        "csv_filename": "ts_demand_h2.csv",
        "nominal_value": 1,
        "column_title": "Hydrogen load",
        "path": my_path
    },
    "from_grid": {
        "component": "supply",
        "bus_out": "bel",
        "output_max": 5000000,
        "variable_costs": 0.00016,
        "fs_component_name": "h2_storage",
        "fs_attribute_name": "storage_level",
        "fs_threshold": 200,
        "fs_low_art_cost": -0.001,
        "fs_high_art_cost": 50,
        "dependency_flow_costs": ("from_grid", "bel"),
        "dependency_flow_emissions": ("from_grid", "bel")
    },
    "to_grid": {
        "component": "sink",
        "bus_in": "bel",
        "artificial_costs": 10,
        "dependency_flow_costs": ("bel", "to_grid"),
        "dependency_flow_emissions": ("bel", "to_grid")
    },
    "h2_storage": {
        "component": "storage_h2",
        "bus_in": "bh2_lp",
        "bus_out": "bh2_lp",
        "p_min": 5,
        "p_max": 450,
        "storage_capacity": 500,
        "life_time": 30,
        "capex": {
            "key": [
                "poly",
                "spec"
            ],
            "fitting_value": [
                [
                    604.6,
                    0.5393
                ],
                "cost"
            ],
            "dependant_value": [
                "p_max",
                "storage_capacity"
            ]
        },
        "opex": {
            "key": "spec",
            "fitting_value": 0.01,
            "dependant_value": "capex"
        }
    },
    "h2_compressor": {
        "component": "compressor_h2",
        "bus_h2_in": "bh2_lp",
        "bus_h2_out": "bh2_hp",
        "bus_el": "bel",
        "m_flow_max": 67.2,
        "life_time": 20,
        "fs_component_name": [
            "h2_storage",
            None
        ],
        "fs_attribute_name": [
            "pressure",
            700
        ],
        "capex": {
            "key": "free",
            "fitting_value": [
                34592,
                0.6468
            ],
            "dependant_value": "m_flow_max"
        },
        "opex": {
            "key": "spec",
            "fitting_value": 0.04,
            "dependant_value": "capex"
        }
    }
}

sim_params = {
    'start_date': '1/1/2019',
    'n_intervals': 10,
    'interval_time': 60,
    'interest_rate': 0.03,
    'print_progress': False,
    'show_debug_flag': False
}

mymodel = {
    'busses': busses,
    'components': components,
    'sim_params': sim_params,
}
