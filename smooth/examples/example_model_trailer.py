"""
This example demonstrates the basic usage of hydrogen trailers in an energy system,
and how they should be included in the model definition. The energy system in this
example has three production sites, with a trailer delivering from the first production
site to a refuelling station, and another trailer delivering from the other two production
sites to another refuelling station. Below, notable components in the model definition
(in relation to hydrogen trailers) are outlined.

Gate at production sites
------------------------
A gate component is used at the production sites to allow for produced hydrogen to be
directly sent to the delivery, without having to go through the storage. This is
necessary to ensure that the buses coming out of the storage and coming straight
from the electrolyzer are the same, because the buses entering and leaving the
storage are distinct in this case.

.. code:: bash

components.append({
    'component': 'gate',
    'name': 'storage_gate_prod_site_1',
    'bus_in': 'bh2_300_prod_site_1',
    'bus_out': 'bh2_300_prod_site_1_for_dlvry',
    'max_input': 1000e3,
    'artificial_costs': -200,
    'dependency_flow_costs': ('bh2_300_prod_site_1', 'storage_gate_prod_site_1'),
})

Trailer gate
------------
A trailer gate component is defined to limit the flows into the trailer
components depending on whether delivery is possible or not. This can
be defined as follows:

.. code:: bash

components.append({
    'component': 'trailer_gate',
    'name': 'h2_gate_dlvry_to_HRS_1',
    'bus_in': 'bh2_300_prod_site_1',
    'bus_out': 'bh2_300_dlvry_HRS_1',
    'max_input': 1000e6,
    'trailer_distance': 20,  # 20 km
    'driver_costs': 0,
    'variable_costs': 35 / 100 * 1.2,
    'dependency_flow_costs': ('h2_gate_dlvry_to_HRS_1', 'bh2_300_dlvry_HRS_1'),
    # Foreign states
    'fs_component_name': ['trailer_HRS_1', 'storage_prod_site_1', 'storage_prod_site_1',
                          'storage_prod_site_1', 'storage_HRS_1', 'storage_HRS_1',
                          'trailer_HRS_1'],
    'fs_attribute_name': ['fs_origin_available_kg', 'storage_level', 'storage_level_min',
                          'storage_capacity', 'storage_level', 'storage_capacity',
                          'fs_destination_storage_threshold']
})

Trailer delivery from single origin
-----------------------------------
The delivery from production site 1 to refuelling station 1 is achieved
using the below component, which states that if the destination storage
falls below 30%, the system is incentivised to pick up hydrogen from
the production site.

.. code:: bash

components.append({
    'component': 'trailer_h2_delivery_single',
    'name': 'trailer_HRS_1',
    'trailer_capacity': 900,
    'bus_in': 'bh2_300_dlvry_HRS_1',
    'bus_out': 'bh2_300_HRS_1',
    # Foreign states
    'fs_component_name': ['storage_prod_site_1', 'storage_prod_site_1', 'storage_prod_site_1',
                          'storage_HRS_1', 'storage_HRS_1'],
    'fs_attribute_name': ['storage_level', 'storage_level_min', 'storage_capacity',
                          'storage_level', 'storage_capacity'],
    'fs_destination_storage_threshold': 0.3,
    'dependency_flow_costs': ('bh2_300_dlvry_HRS_1', 'trailer_HRS_1')
})

Trailer delivery from multiple origins
--------------------------------------
This is defined in a similar way to the above trailer component, but it
also considers both production site 2 and 3. It determines which one
should be collected from (if the destination storage is running low) for
the given timestep, based on storage availability.

.. code:: bash

components.append({
    'component': 'trailer_h2_delivery',
    'name': 'trailer_HRS_2',
    'trailer_capacity': 900,
    'bus_in': 'bh2_300_dlvry_HRS_2',
    'bus_out': 'bh2_300_HRS_2',
    # Foreign states
    'fs_component_name': ['storage_prod_site_2', 'storage_prod_site_3',
                          'storage_prod_site_2', 'storage_prod_site_3',
                          'storage_prod_site_2', 'storage_prod_site_3',
                          'storage_HRS_2', 'storage_HRS_2'],
    'fs_attribute_name': ['storage_level', 'storage_level',
                          'storage_level_min', 'storage_level_min',
                          'storage_capacity', 'storage_capacity',
                          'storage_level', 'storage_capacity'],
    'fs_destination_storage_threshold': 0.3,
    'dependency_flow_costs': ('bh2_300_dlvry_HRS_2', 'trailer_HRS_2')
})
"""
import os

# Define where Python should look for csv files
my_path = os.path.join(os.path.dirname(__file__), 'example_timeseries')

""" Create busses """
# create hydrogen bus
busses = ['bel_prod_site_1', 'bh2_40_prod_site_1', 'bh2_300_prod_site_1',
          'bh2_300_prod_site_1_for_dlvry', 'bel_prod_site_2', 'bh2_40_prod_site_2',
          'bh2_300_prod_site_2', 'bh2_300_prod_site_2_for_dlvry', 'bel_prod_site_3',
          'bh2_40_prod_site_3', 'bh2_300_prod_site_3', 'bh2_300_prod_site_3_for_dlvry',
          'bh2_300_dlvry_HRS_1', 'bh2_300_HRS_1', 'bh2_300_dlvry_HRS_2', 'bh2_300_HRS_2',
          'bh2_300_HRS_1_2', 'bh2_350_HRS_1', 'bel_HRS_1', 'bh2_350_HRS_plön',
          'bh2_300_HRS_2_2', 'bh2_350_HRS_2', 'bel_HRS_2']


""" Define components """
components = list()

# ------------------- PRODUCTION SITE 1 -------------------
# WIND FARM
components.append({
    'component': 'energy_source_from_csv',
    'name': 'wind_output_prod_site_1',
    'bus_out': 'bel_prod_site_1',
    'csv_filename': 'ts_wind_1kW_prod_site_1.csv',
    'csv_separator': ',',
    'nominal_value': 10e3,  # 10 MW
    'column_title': 'Power output in W',
    'path': my_path
})

# ELECTROLYZER
components.append({
    'component': 'electrolyzer',
    'name': 'ely_prod_site_1',
    'bus_el': 'bel_prod_site_1',
    'bus_h2': 'bh2_40_prod_site_1',
    'power_max': 5000e3,
    'temp_init': 293.15,
    'life_time': 22.86,
    'capex': {
        'key': 'spec',
        'fitting_value': 731.46 / 1000,
        'dependant_value': 'power_max',
    },
    'opex': {
        'key': 'spec',
        'fitting_value': 0.04,
        'dependant_value': 'capex',
    }
})

# COMPRESSOR (40-300 BAR)
components.append({
    'component': 'compressor_h2',
    'name': 'h2_compressor_prod_site_1',
    # Busses
    'bus_h2_in': 'bh2_40_prod_site_1',
    'bus_h2_out': 'bh2_300_prod_site_1',
    'bus_el': 'bel_prod_site_1',
    # Parameters
    'm_flow_max': 100,
    'life_time': 20,
    # Foreign states
    'fs_component_name': ['ely_prod_site_1', None],
    'fs_attribute_name': ['fs_pressure', 300],
    # Financials
    'capex': {
        'key': 'free',
        'fitting_value': [28063, 0.6378],
        'dependant_value': 'm_flow_max'
    },
    'opex': {
        'key': 'spec',
        'fitting_value': 0.04,
        'dependant_value': 'capex'
    }
})

# STORAGE (300 BAR)
components.append({
    'component': 'storage_h2',
    'name': 'storage_prod_site_1',
    'bus_in': 'bh2_300_prod_site_1',
    'bus_out': 'bh2_300_prod_site_1_for_dlvry',
    'p_min': 5,
    'p_max': 300,
    'storage_capacity': 5000,
    'life_time': 20,
    'initial_storage_factor': 0.5,
    'vac_in': -100,
    'dependency_flow_costs': ('bh2_300_prod_site_1', 'storage_prod_site_1'),
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

# # PRODUCTION SITE 1 GATE H2
# For hydrogen that is produced and directly sent to delivery
components.append({
    'component': 'gate',
    'name': 'storage_gate_prod_site_1',
    'bus_in': 'bh2_300_prod_site_1',
    'bus_out': 'bh2_300_prod_site_1_for_dlvry',
    'max_input': 1000e3,
    'artificial_costs': -200,
    'dependency_flow_costs': ('bh2_300_prod_site_1', 'storage_gate_prod_site_1'),
})

# # SINK H2 PRODUCTION SITE 1
# If too much hydrogen is produced which cannot fit in the storage/be delivered
components.append({
    'component': 'sink',
    'name': 'h2_sink_prod_site_1',
    'bus_in': 'bh2_300_prod_site_1',
    'input_max': 8000,
    'artificial_costs': 2500,
    'dependency_flow_costs': ('bh2_300_prod_site_1', 'h2_sink_prod_site_1'),
    'variable_costs': 0
})

# # SINK EL PRODUCTION SITE 1
# For excess electricity that is not used to produced hydrogen/power the compressor
components.append({
    'component': 'sink',
    'name': 'el_sink_prod_site_1',
    'bus_in': 'bel_prod_site_1',
    'input_max': 800000e3,
    'artificial_costs': 5000,
    'dependency_flow_costs': ('bel_prod_site_1', 'el_sink_prod_site_1'),
    'variable_costs': 0
})

# ------------------- PRODUCTION SITE 2 -------------------
# WIND FARM
components.append({
    'component': 'energy_source_from_csv',
    'name': 'wind_output_prod_site_2',
    'bus_out': 'bel_prod_site_2',
    'csv_filename': 'ts_wind_1kW_prod_site_2.csv',
    'csv_separator': ',',
    'nominal_value': 5e3,  # 10 MW
    'column_title': 'Power output in W',
    'path': my_path
})

# ELECTROLYZER
components.append({
    'component': 'electrolyzer',
    'name': 'ely_prod_site_2',
    'bus_el': 'bel_prod_site_2',
    'bus_h2': 'bh2_40_prod_site_2',
    'power_max': 5000e3,
    'temp_init': 293.15,
    'life_time': 22.86,
    'capex': {
        'key': 'spec',
        'fitting_value': 731.46 / 1000,
        'dependant_value': 'power_max',
    },
    'opex': {
        'key': 'spec',
        'fitting_value': 0.04,
        'dependant_value': 'capex',
    }
})

# COMPRESSOR (40-300 BAR)
components.append({
    'component': 'compressor_h2',
    'name': 'h2_compressor_prod_site_2',
    # Busses
    'bus_h2_in': 'bh2_40_prod_site_2',
    'bus_h2_out': 'bh2_300_prod_site_2',
    'bus_el': 'bel_prod_site_2',
    # Parameters
    'm_flow_max': 100,
    'life_time': 20,
    # Foreign states
    'fs_component_name': ['ely_prod_site_2', None],
    'fs_attribute_name': ['fs_pressure', 300],
    # Financials
    'capex': {
        'key': 'free',
        'fitting_value': [28063, 0.6378],
        'dependant_value': 'm_flow_max'
    },
    'opex': {
        'key': 'spec',
        'fitting_value': 0.04,
        'dependant_value': 'capex'
    }
})

# STORAGE (300 BAR)
components.append({
    'component': 'storage_h2',
    'name': 'storage_prod_site_2',
    'bus_in': 'bh2_300_prod_site_2',
    'bus_out': 'bh2_300_prod_site_2_for_dlvry',
    'p_min': 5,
    'p_max': 300,
    'storage_capacity': 5000,
    'life_time': 20,
    'initial_storage_factor': 0.5,
    'vac_in': -100,
    'dependency_flow_costs': ('bh2_300_prod_site_2', 'storage_prod_site_2'),
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

# # PRODUCTION SITE 2 GATE H2
# For hydrogen that is produced and directly sent to delivery
components.append({
    'component': 'gate',
    'name': 'storage_gate_prod_site_2',
    'bus_in': 'bh2_300_prod_site_2',
    'bus_out': 'bh2_300_prod_site_2_for_dlvry',
    'max_input': 1000e3,
    'artificial_costs': -200,
    'dependency_flow_costs': ('bh2_300_prod_site_2', 'storage_gate_prod_site_2'),
})

# # SINK H2 PRODUCTION SITE 2
# If too much hydrogen is produced which cannot fit in the storage/be delivered
components.append({
    'component': 'sink',
    'name': 'h2_sink_prod_site_2',
    'bus_in': 'bh2_300_prod_site_2',
    'input_max': 8000,
    'artificial_costs': 2500,
    'dependency_flow_costs': ('bh2_300_prod_site_2', 'h2_sink_prod_site_2'),
    'variable_costs': 0
})

# # SINK EL PRODUCTION SITE 2
# For excess electricity that is not used to produced hydrogen/power the compressor
components.append({
    'component': 'sink',
    'name': 'el_sink_prod_site_2',
    'bus_in': 'bel_prod_site_2',
    'input_max': 800000e3,
    'artificial_costs': 5000,
    'dependency_flow_costs': ('bel_prod_site_2', 'el_sink_prod_site_2'),
    'variable_costs': 0
})

# ------------------- PRODUCTION SITE 3 -------------------
# PV PLANT
components.append({
    'component': 'energy_source_from_csv',
    'name': 'pv_output_prod_site_3',
    'bus_out': 'bel_prod_site_3',
    'csv_filename': 'ts_pv_1kW_prod_site_3.csv',
    'csv_separator': ',',
    'nominal_value': 5000,  # 5 MW
    'life_time': 26.42,
    'column_title': 'Power output in W',
    'path': my_path
})

# ELECTROLYZER
components.append({
    'component': 'electrolyzer',
    'name': 'ely_prod_site_3',
    'bus_el': 'bel_prod_site_3',
    'bus_h2': 'bh2_40_prod_site_3',
    'power_max': 5000e3,
    'temp_init': 293.15,
    'life_time': 22.86,
    'capex': {
        'key': 'spec',
        'fitting_value': 731.46 / 1000,
        'dependant_value': 'power_max',
    },
    'opex': {
        'key': 'spec',
        'fitting_value': 0.04,
        'dependant_value': 'capex',
    }
})

# COMPRESSOR (40-300 BAR)
components.append({
    'component': 'compressor_h2',
    'name': 'h2_compressor_prod_site_3',
    # Busses
    'bus_h2_in': 'bh2_40_prod_site_3',
    'bus_h2_out': 'bh2_300_prod_site_3',
    'bus_el': 'bel_prod_site_3',
    # Parameters
    'm_flow_max': 100,
    'life_time': 20,
    # Foreign states
    'fs_component_name': ['ely_prod_site_3', None],
    'fs_attribute_name': ['fs_pressure', 300],
    # Financials
    'capex': {
        'key': 'free',
        'fitting_value': [28063, 0.6378],
        'dependant_value': 'm_flow_max'
    },
    'opex': {
        'key': 'spec',
        'fitting_value': 0.04,
        'dependant_value': 'capex'
    }
})

# STORAGE (300 BAR)
components.append({
    'component': 'storage_h2',
    'name': 'storage_prod_site_3',
    'bus_in': 'bh2_300_prod_site_3',
    'bus_out': 'bh2_300_prod_site_3_for_dlvry',
    'p_min': 5,
    'p_max': 300,
    'storage_capacity': 5000,
    'life_time': 20,
    'initial_storage_factor': 0.5,
    'vac_in': -100,
    'dependency_flow_costs': ('bh2_300_prod_site_3', 'storage_prod_site_3'),
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

# # PRODUCTION SITE 3 GATE H2
# For hydrogen that is produced and directly sent to delivery
components.append({
    'component': 'gate',
    'name': 'storage_gate_prod_site_3',
    'bus_in': 'bh2_300_prod_site_3',
    'bus_out': 'bh2_300_prod_site_3_for_dlvry',
    'max_input': 1000e3,
    'artificial_costs': -200,
    'dependency_flow_costs': ('bh2_300_prod_site_3', 'storage_gate_prod_site_3'),
})

# # SINK H2 PRODUCTION SITE 3
# If too much hydrogen is produced which cannot fit in the storage/be delivered
components.append({
    'component': 'sink',
    'name': 'h2_sink_prod_site_3',
    'bus_in': 'bh2_300_prod_site_3',
    'input_max': 8000,
    'artificial_costs': 2500,
    'dependency_flow_costs': ('bh2_300_prod_site_3', 'h2_sink_prod_site_3'),
    'variable_costs': 0
})

# # SINK EL PRODUCTION SITE 3
# For excess electricity that is not used to produced hydrogen/power the compressor
components.append({
    'component': 'sink',
    'name': 'el_sink_prod_site_3',
    'bus_in': 'bel_prod_site_3',
    'input_max': 800000e3,
    'artificial_costs': 5000,
    'dependency_flow_costs': ('bel_prod_site_3', 'el_sink_prod_site_3'),
    'variable_costs': 0
})

# ------------------ DELIVERY FROM PRODUCTION SITE 1 TO HRS 1 ------------------

# # PROD SITE 1 TRAILER GATE H2 FOR DELIVERY TO HRS 1
components.append({
    'component': 'trailer_gate',
    'name': 'h2_gate_dlvry_to_HRS_1',
    'bus_in': 'bh2_300_prod_site_1',
    'bus_out': 'bh2_300_dlvry_HRS_1',
    'max_input': 1000e6,
    'trailer_distance': 20,  # 20 km
    'driver_costs': 0,
    'variable_costs': 35 / 100 * 1.2,
    'dependency_flow_costs': ('h2_gate_dlvry_to_HRS_1', 'bh2_300_dlvry_HRS_1'),
    # Foreign states
    'fs_component_name': ['trailer_HRS_1', 'storage_prod_site_1', 'storage_prod_site_1',
                          'storage_prod_site_1', 'storage_HRS_1', 'storage_HRS_1',
                          'trailer_HRS_1'],
    'fs_attribute_name': ['fs_origin_available_kg', 'storage_level', 'storage_level_min',
                          'storage_capacity', 'storage_level', 'storage_capacity',
                          'fs_destination_storage_threshold']
})

# TRAILER DELIVERY TO HRS 1
components.append({
    'component': 'trailer_h2_delivery_single',
    'name': 'trailer_HRS_1',
    'trailer_capacity': 900,
    'bus_in': 'bh2_300_dlvry_HRS_1',
    'bus_out': 'bh2_300_HRS_1',
    # Foreign states
    'fs_component_name': ['storage_prod_site_1', 'storage_prod_site_1', 'storage_prod_site_1',
                          'storage_HRS_1', 'storage_HRS_1'],
    'fs_attribute_name': ['storage_level', 'storage_level_min', 'storage_capacity',
                          'storage_level', 'storage_capacity'],
    'fs_destination_storage_threshold': 0.3,
    'dependency_flow_costs': ('bh2_300_dlvry_HRS_1', 'trailer_HRS_1')
})

# ------------------ DELIVERY FROM PRODUCTION SITES 2&3 TO HRS 2 ------------------

# # PROD SITE 2 TRAILER GATE H2 FOR DELIVERY TO HRS 2
components.append({
    'component': 'trailer_gate',
    'name': 'h2_gate_wind_dlvry_to_HRS_2',
    'bus_in': 'bh2_300_prod_site_2',
    'bus_out': 'bh2_300_dlvry_HRS_2',
    'max_input': 1000e6,
    'trailer_distance': 25,  # 25 km
    'driver_costs': 0,
    'variable_costs': 35 / 100 * 1.2,
    'dependency_flow_costs': ('h2_gate_wind_dlvry_to_HRS_2', 'bh2_300_dlvry_HRS_2'),
    # Foreign states
    'fs_component_name': ['trailer_HRS_2', 'storage_prod_site_2', 'storage_prod_site_2',
                          'storage_prod_site_2', 'storage_HRS_2', 'storage_HRS_2',
                          'trailer_HRS_2'],
    'fs_attribute_name': ['fs_origin_available_kg', 'storage_level', 'storage_level_min',
                          'storage_capacity', 'storage_level', 'storage_capacity',
                          'fs_destination_storage_threshold'],
})

# # PROD SITE 3 TRAILER GATE H2 FOR DELIVERY TO HRS 2
components.append({
    'component': 'trailer_gate',
    'name': 'h2_gate_pv_dlvry_to_HRS_2',
    'bus_in': 'bh2_300_prod_site_3',
    'bus_out': 'bh2_300_dlvry_HRS_2',
    'max_input': 1000e6,
    'trailer_distance': 18,  # 18 km
    'driver_costs': 0,
    'variable_costs': 35 / 100 * 1.2,
    'dependency_flow_costs': ('h2_gate_pv_dlvry_to_HRS_2', 'bh2_300_dlvry_HRS_2'),
    # Foreign states
    'fs_component_name': ['trailer_HRS_2', 'storage_prod_site_3', 'storage_prod_site_3',
                          'storage_prod_site_3', 'storage_HRS_2', 'storage_HRS_2',
                          'trailer_HRS_2'],
    'fs_attribute_name': ['fs_origin_available_kg', 'storage_level', 'storage_level_min',
                          'storage_capacity', 'storage_level', 'storage_capacity',
                          'fs_destination_storage_threshold'],
})

# TRAILER DELIVERY TO HRS 2
components.append({
    'component': 'trailer_h2_delivery',
    'name': 'trailer_HRS_2',
    'trailer_capacity': 900,
    'bus_in': 'bh2_300_dlvry_HRS_2',
    'bus_out': 'bh2_300_HRS_2',
    # Foreign states
    'fs_component_name': ['storage_prod_site_2', 'storage_prod_site_3',
                          'storage_prod_site_2', 'storage_prod_site_3',
                          'storage_prod_site_2', 'storage_prod_site_3',
                          'storage_HRS_2', 'storage_HRS_2'],
    'fs_attribute_name': ['storage_level', 'storage_level',
                          'storage_level_min', 'storage_level_min',
                          'storage_capacity', 'storage_capacity',
                          'storage_level', 'storage_capacity'],
    'fs_destination_storage_threshold': 0.3,
    'dependency_flow_costs': ('bh2_300_dlvry_HRS_2', 'trailer_HRS_2')
})

# ----------------------------------- HRS 1 -----------------------------------

# STORAGE HRS 1
components.append({
    'component': 'storage_h2',
    'name': 'storage_HRS_1',
    'bus_in': 'bh2_300_HRS_1',
    'bus_out': 'bh2_300_HRS_1_2',
    'p_min': 5,
    'p_max': 300,
    'storage_capacity': 300,
    'initial_storage_factor': 0.5,
    'dependency_flow_costs': ('bh2_300_HRS_1', 'storage_HRS_1'),
    'vac_in': -100,
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

# GATE HRS 1
# Gate for hydrogen directly meeting the demand instead of passing through the storage
components.append({
    'component': 'gate',
    'name': 'h2_gate_HRS_1',
    'bus_in': 'bh2_300_HRS_1',
    'bus_out': 'bh2_300_HRS_1_2',
    'max_input': 1000e3,
    'artificial_costs': -150,
    'dependency_flow_costs': ('bh2_300_HRS_1', 'h2_gate_HRS_1'),
})

# COMPRESSOR HRS 1 (300-350 BAR)
components.append({
    'component': 'compressor_h2',
    'name': 'h2_compressor_HRS_1_350',
    # Busses
    'bus_h2_in': 'bh2_300_HRS_1_2',
    'bus_h2_out': 'bh2_350_HRS_1',
    # Parameters
    'bus_el': 'bel_HRS_1',
    'm_flow_max': 100,
    'life_time': 20,
    # Foreign states
    'fs_component_name': ['storage_HRS_1', None],
    'fs_attribute_name': ['pressure', 350],
    # Financials
    'capex': {
        'key': 'free',
        'fitting_value': [28063, 0.6378],
        'dependant_value': 'm_flow_max'
    },
    'opex': {
        'key': 'spec',
        'fitting_value': 0.04,
        'dependant_value': 'capex'
    }
})

# EL GRID HRS 1
components.append({
    'component': 'supply',
    'name': 'el_grid_HRS_1',
    'bus_out': 'bel_HRS_1',
    'output_max': 1000e6,
    'variable_costs': 18.55 / 100 / 1000,  # 18.55 ct/kWh
    'artificial_costs': 2500,
    'dependency_flow_costs': ('el_grid_HRS_1', 'bel_HRS_1')
})

# H2 DEMAND 1
components.append({
    'component': 'energy_demand_from_csv',
    'name': 'h2_demand_HRS_1',
    'bus_in': 'bh2_350_HRS_1',
    'csv_filename': 'ts_h2_demand_HRS_1.csv',
    'nominal_value': 1,
    'column_title': 'H2 demand in kg',
    'path': my_path
})

# ----------------------------------- HRS 2 -----------------------------------

# STORAGE HRS 2
components.append({
    'component': 'storage_h2',
    'name': 'storage_HRS_2',
    'bus_in': 'bh2_300_HRS_2',
    'bus_out': 'bh2_300_HRS_2_2',
    'p_min': 5,
    'p_max': 300,
    'storage_capacity': 300,
    'initial_storage_factor': 0.5,
    'dependency_flow_costs': ('bh2_300_HRS_2', 'storage_HRS_2'),
    'vac_in': -100,
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

# GATE HRS 2
# Gate for hydrogen directly meeting the demand instead of passing through the storage
components.append({
    'component': 'gate',
    'name': 'h2_gate_HRS_2',
    'bus_in': 'bh2_300_HRS_2',
    'bus_out': 'bh2_300_HRS_2_2',
    'max_input': 1000e3,
    'artificial_costs': -150,
    'dependency_flow_costs': ('bh2_300_HRS_2', 'h2_gate_HRS_2'),
})

# COMPRESSOR HRS 2 (300-350 BAR)
components.append({
    'component': 'compressor_h2',
    'name': 'h2_compressor_HRS_2_350',
    # Busses
    'bus_h2_in': 'bh2_300_HRS_2_2',
    'bus_h2_out': 'bh2_350_HRS_2',
    # Parameters
    'bus_el': 'bel_HRS_2',
    'm_flow_max': 100,
    'life_time': 20,
    # Foreign states
    'fs_component_name': ['storage_HRS_2', None],
    'fs_attribute_name': ['pressure', 350],
    # Financials
    'capex': {
        'key': 'free',
        'fitting_value': [28063, 0.6378],
        'dependant_value': 'm_flow_max'
    },
    'opex': {
        'key': 'spec',
        'fitting_value': 0.04,
        'dependant_value': 'capex'
    }
})

# EL GRID HRS 2
components.append({
    'component': 'supply',
    'name': 'el_grid_HRS_2',
    'bus_out': 'bel_HRS_2',
    'output_max': 1000e6,
    'variable_costs': 18.55 / 100 / 1000,  # 18.55 ct/kWh
    'artificial_costs': 2500,
    'dependency_flow_costs': ('el_grid_HRS_2', 'bel_HRS_2')
})

# H2 DEMAND 1
components.append({
    'component': 'energy_demand_from_csv',
    'name': 'h2_demand_HRS_2',
    'bus_in': 'bh2_350_HRS_2',
    'csv_filename': 'ts_h2_demand_HRS_2.csv',
    'nominal_value': 1,
    'column_title': 'H2 demand in kg',
    'path': my_path
})

sim_params = {
    'start_date': '1/1/2019',
    'n_intervals': 24*7,
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
