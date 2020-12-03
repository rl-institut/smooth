"""
This example is here to show how the various cost fitting methods can be
implemented in the model definition. It should be noted that the actual
cost values chosen here are arbitrary. The fitting method of the cost is
chosen by the key, and the possible fitting methods are:

Fixed cost (*'fix'*)
--------------------
Here, no fitting is done. The value given in the definition is the *cost* value.
The cost value for CAPEX is taken in EUR while the cost value for OPEX is taken
in EUR/a.

.. code:: bash

    cost = cost

An example of this could be as follows for a compressor component:

    .. code:: bash

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
                'key': 'fix',
                'fitting_value': None,
                'dependant_value': None,
                'cost': 2000
            },
            'opex': {
                'key': 'fix',
                'fitting_value': None,
                'dependant_value': None,
                'cost': 200
            }
         })

Here the cost of the compressor is independant of any other parameter
(*fitting_value/dependant_value* = None), at 2000 EUR for the CAPEX
and 200 EUR/a for the OPEX.

Specific cost (*'spec'*)
----------------------
The specific cost key means that the cost is dependant on one component
parameter (e.g. EUR/kW). The value of the *dependant_value* is the parameter
name in the form of a string (e.g. *'power_max'*). The *fitting_value* is
then multiplied with the dependant value to obtain the final costs.

.. code:: bash

    cost = fitting_value * component[dependant_value]

An example of this can be seen with the following PV component:

.. code:: bash

    components.append({
        'component': 'energy_source_from_csv',
        'name': 'pv_output',
        'bus_out': 'bel',
        'csv_filename': 'ts_pv_1kW.csv',
        'csv_separator': ',',
        'nominal_value': 100,
        'column_title': 'Power output [W]',
        'path': my_path,
        'life_time': 20,
        'capex': {
            'key': 'spec',
            'fitting_value': 975.57,
            'dependant_value': 'nominal_value',
        },
        'opex': {
            'key': 'spec',
            'fitting_value': 0.02,
            'dependant_value': 'capex',
        }
    })

This implies that the CAPEX of the PV system is 975.57 EUR/*nominal_value*
where the *nominal_value* is the number of kilowatts, and that the
OPEX is 2% of the CAPEX per annum.

Exponential cost (*'exp'*)
------------------------
The exponential fitting of the cost means that two or three entries can be
given as the *fitting_value*, and the costs are then calculated in the following
way:

.. code:: bash

    for two fitting values [fv_1, fv_2]:
    cost = fv_1 * exp(dependant_value * fv_2)

    for three fitting values [fv_1, fv_2, fv_3]:
    cost = fv_1 + fv_2 * exp(dependant_value * fv_3)

An example of this is shown with a wind component:

.. code:: bash

    components.append({
        'component': 'energy_source_from_csv',
        'name': 'wind_output',
        'bus_out': 'bel',
        'csv_filename': 'ts_wind_1kW.csv',
        'csv_separator': ',',
        'nominal_value': 10,
        'column_title': 0,
        'path': my_path,
        'life_time': 10,
        'capex': {
            'key': 'exp',
            'fitting_value': [750, 0.5],
            'dependant_value': 'nominal_value',
        },
        'opex': {
            'key': 'spec',
            'fitting_value': 0.02,
            'dependant_value': 'capex',
        }
    })

This demonstrates that the CAPEX of the wind system costs :math:`750 \\cdot e^{\\frac{nv}{2}}`
EUR, and that the OPEX costs 2% of the CAPEX per annum, where *nv* is the *nominal_value*.

Polynomial cost (*'poly'*)
--------------------------
For the polynomial cost function, an arbitrary number of fitting values are defined
and the cost is then calculated as follows:

.. code:: bash

    for an arbitrary number of fitting values [fv_1, fv_2, fv_3, ..., fv_n]
    cost = fv_1 + fv_2 * dependant_value**1 + fv_3 * dependant_value**2 + ...
           + fv_n * dependant_value**(n-1)

This can be demonstrated with the costs of a storage component:

.. code:: bash

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
            'key': 'poly',
            'fitting_value': [604.6, 0.5393],
            'dependant_value': 'p_max'
        },
        'opex': {
            'key': 'spec',
            'fitting_value': 0.01,
            'dependant_value': 'capex'
        },
    })

Here, the costs for the storage component are :math:`604.6 + (p_{max} \\cdot {0.5393})` for
the CAPEX (EUR) and the OPEX is 1% of the CAPEX per annum.

Free cost (*'free'*)
--------------------
The free cost is similar to the polynomial fitting, but here the exponents can be chosen
freely:

.. code:: bash

    for an even number of fitting values [fv_1, fv_2, fv_3, ..., fv_n]
    cost = fv_1 * dependant_value**fv_2 + fv_3 * dependant_value**fv_4 + ...
           + fv_(n-1) * dependant_value**fv_n

This is also demonstrated with the storage component:

.. code:: bash

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
            'key': 'free',
            'fitting_value': [600, 0.5, 0.8, 0.2],
            'dependant_value': 'p_max'
        },
        'opex': {
            'key': 'spec',
            'fitting_value': 0.01,
            'dependant_value': 'capex'
        },
    })

This means that the CAPEX for the storage would be
:math:`600 \\cdot p_{max}^{0.5} + 0.8 \\cdot p_{max}^{0.2}` (EUR)
and the OPEX would be 1% of the CAPEX per annum.

Addition of two functions
-------------------------
It is also possible to add two functions together if the cost equation requires
this. An example of this can again be seen in a storage component where both the
specific and polynomial fittings are used:

.. code:: bash

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
            'key': ['spec', 'poly'],
            'fitting_value': [600, ['cost', 100]],
            'dependant_value': ['storage_capacity', 'p_max'],
        },
        'opex': {
            'key': 'spec',
            'fitting_value': 0.01,
            'dependant_value': 'capex'
        },
    })

The above example entails that the CAPEX of the storage component here is
:math:`600 \\cdot s_{c} + 100 \\cdot p_{max}`. In
stages it can be broken down as follows:

* The first part of the cost is calculated using the specific function
  (:math:`600 \\cdot s_{c}`).
* Then the value for this is taken as the new *'cost'* value which can
  be then used as a free value for further calculations.
* The previously calculated *'cost'* value is then used as the first free
  variable in a polynomial function to obtain
  :math:`600 \\cdot s_{c} + 100 \\cdot p_{max}`.

Economy of scale
----------------
There is also the option to include the economy of scale in the costs, and it
can be defined as follows:

.. code:: bash

    components.append({
        'component': 'supply',
        'name': 'from_grid',
        'bus_out': 'bel',
        'output_max': 1200e3,
        'variable_costs': 0.00001,
        'dependency_flow_costs': ('from_grid', 'bel'),
        'life_time': 1,
        'capex': {
            'key': 'variable',
            'var_dict_dependency': 'output_max',
            'var_dicts':
                [
                    {
                        'low_threshold': 0,
                        'high_threshold': 900e3,
                        'key': 'free',
                        'fitting_value': [2, 3],
                        'dependant_value': 'output_max'
                    },
                    {
                        'low_threshold': 1000e3,
                        'high_threshold': 5000e3,
                        'key': ['spec', 'poly'],
                        'fitting_value': [10, ['cost', 1]],
                        'dependant_value': ['output_max', 'life_time'],
                    },
                    {
                        'low_threshold': 5000e3,
                        'high_threshold': float('inf'),
                        'key': 'spec',
                        'fitting_value': 50,
                        'dependant_value': 'output_max',
                    },
                ],
        },
        'opex': {
            'key': 'variable',
            'var_dict_dependency': 'output_max',
            'var_dicts': [
                {
                    'low_threshold': 0,
                    'high_threshold': 1000e3,
                    'key': 'spec',
                    'fitting_value': 0.04,
                    'dependant_value': 'capex',
                },
                {
                    'low_threshold': 1000e3,
                    'high_threshold': 5000e3,
                    'key': 'spec',
                    'fitting_value': 0.02,
                    'dependant_value': 'capex',
                },
            ]
        },
    })

This shows the varying CAPEX and OPEX costs of the electricity supply from
the grid, depending on its size. If the key 'variable' is defined, multiple
CAPEX or OPEX costs can be defined depending on the value of one attribute
of the component. This attribute is defined for the 'var_dict_dependency' key.

The specific dict that is used in the system is chosen if:

.. code:: bash

    low_threshold <= value(var_capex_dependency) < high_threshold

It should be noted that the number of dicts can be chosen freely, but
they must be defined in ascending order. Also, gaps are fine between
defined ranges whereas overlapping ranges are not possible. The above
example states that:

* If the chosen maximum output power from the grid is less than 900 kW, the
  CAPEX is :math:`2 \\cdot output_{max}^{3}` EUR
* If the chosen maximum output power from the grid is between 1000 kW and
  5000 kW, the CAPEX is :math:`10 \\cdot output_{max} + lifetime` EUR
* If the chosen maximum output power from the grid is above 5000 kW, the
  CAPEX is :math:`50 \\cdot output_{max}` EUR
* If the chosen maximum output power from the grid is less than 1000 kW, the
  OPEX is 4% of the CAPEX
* If the chosen maximum output power from the grid is between 1000 kW and
  5000 kW, the OPEX is 2% of the CAPEX
"""

import os

# Define where Python should look for csv files
my_path = os.path.join(os.path.dirname(__file__), 'example_timeseries')

# Create busses list
busses = ['bel', 'bh2_lp', 'bh2_hp', 'bth']

# Define components list
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
    'name': 'pv_output',
    'bus_out': 'bel',
    'csv_filename': 'ts_pv_1kW.csv',
    'csv_separator': ',',
    'nominal_value': 100,
    'column_title': 'Power output [W]',
    'path': my_path,
    'life_time': 20,
    'capex': {
        'key': 'spec',
        'fitting_value': 975.57,
        'dependant_value': 'nominal_value',
    },
    'opex': {
        'key': 'spec',
        'fitting_value': 0.02,
        'dependant_value': 'capex',
    }
})

components.append({
    'component': 'energy_source_from_csv',
    'name': 'wind_output',
    'bus_out': 'bel',
    'csv_filename': 'ts_wind_1kW.csv',
    'csv_separator': ',',
    'nominal_value': 10,
    'column_title': 0,
    'path': my_path,
    'life_time': 10,
    'capex': {
        'key': 'exp',
        'fitting_value': [750, 0.5],
        'dependant_value': 'nominal_value',
    },
    'opex': {
        'key': 'spec',
        'fitting_value': 0.02,
        'dependant_value': 'capex',
    }
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
    'output_max': 1200e3,
    'variable_costs': 0.00001,
    'dependency_flow_costs': ('from_grid', 'bel'),
    'life_time': 1,
    'capex': {
        'key': 'variable',
        'var_dict_dependency': 'output_max',
        'var_dicts':
            [
                {
                    'low_threshold': 0,
                    'high_threshold': 900e3,
                    'key': 'free',
                    'fitting_value': [2, 3],
                    'dependant_value': 'output_max'
                },
                {
                    'low_threshold': 1000e3,
                    'high_threshold': 5000e3,
                    'key': ['spec', 'poly'],
                    'fitting_value': [10, ['cost', 1]],
                    'dependant_value': ['output_max', 'life_time'],
                },
                {
                    'low_threshold': 5000e3,
                    'high_threshold': float('inf'),
                    'key': 'spec',
                    'fitting_value': 50,
                    'dependant_value': 'output_max',
                },
            ],
    },
    'opex': {
        'key': 'variable',
        'var_dict_dependency': 'output_max',
        'var_dicts': [
            {
                'low_threshold': 0,
                'high_threshold': 1000e3,
                'key': 'spec',
                'fitting_value': 0.04,
                'dependant_value': 'capex',
            },
            {
                'low_threshold': 1000e3,
                'high_threshold': 5000e3,
                'key': 'spec',
                'fitting_value': 0.02,
                'dependant_value': 'capex',
            },
        ]
    },
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
        'key': ['spec', 'poly'],
        'fitting_value': [600, ['cost', 100]],
        'dependant_value': ['storage_capacity', 'p_max'],
    },
    'opex': {
        'key': 'spec',
        'fitting_value': 0.01,
        'dependant_value': 'capex'
    },
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
        'key': 'fix',
        'fitting_value': None,
        'dependant_value': None,
        'cost': 2000
    },
    'opex': {
        'key': 'fix',
        'fitting_value': None,
        'dependant_value': None,
        'cost': 200
    },
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
