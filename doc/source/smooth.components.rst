smooth.components package
=========================
Listed below are components that can already be used in an energy system model (see 
`examples directory <https://github.com/rl-institut/smooth/tree/dev/smooth/examples>`_ for the usage of components 
in an energy system). It is also possible to build your own component if your energy system requires one
that is not already in the framework. 

Building a component
--------------------
In order to build a component, you must do the following:

#. Create a subclass of the mother Component (or External Component) class. 

#. In the :func:`__init__` function, define all parameters that are specific to your component, and set default values.

#. Consider if the component requires variable artificial costs depending on system behaviour. If it does, the method for setting the appropriate costs is defined in the :func:`prepare_simulation` function. 

#. Define any other functions that are specific to your component.

#. All components built in SMOOTH must be created as oemof components to be used in the oemof model (see `oemof-solph's component list <https://oemof-solph.readthedocs.io/en/latest/usage.html#solph-components>`_ to choose the best fitting component. Then create the oemof component in the :func:`create_oemof_model` function, defining all of the necessary parameters.

#. If the states of the component need updating after each time step, specifiy these in the :func:`update_states` function. 

Artificial costs
----------------
The oemof framework 



Submodules
----------

Component
----------------------------------

.. automodule:: smooth.components.component
   :members:
   :undoc-members:
   :show-inheritance:

AC-DC Converter
-------------------------------------------

.. automodule:: smooth.components.component_ac_dc_converter
   :members:
   :undoc-members:
   :show-inheritance:

Air Source Heat Pump
-------------------------------------------

.. automodule:: smooth.components.component_air_source_heat_pump
   :members:
   :undoc-members:
   :show-inheritance:
   
Battery
-------------------------------------------

.. automodule:: smooth.components.component_battery
   :members:
   :undoc-members:
   :show-inheritance:

Compressor (Hydrogen)
--------------------------------------------------

.. automodule:: smooth.components.component_compressor_h2
   :members:
   :undoc-members:
   :show-inheritance:
   
DC-AC Inverter
---------------------------------------

.. automodule:: smooth.components.component_dc_ac_inverter
   :members:
   :undoc-members:
   :show-inheritance:

Electric Heater
------------------------------------------------

.. automodule:: smooth.components.component_electric_heater
   :members:
   :undoc-members:
   :show-inheritance:
   
Electrolyzer (alkaline)
------------------------------------------------

.. automodule:: smooth.components.component_electrolyzer
   :members:
   :undoc-members:
   :show-inheritance:
   
Electrolyzer Waste Heat (alkaline)
------------------------------------------------

.. automodule:: smooth.components.component_electrolyzer_waste_heat
   :members:
   :undoc-members:
   :show-inheritance:

Energy Demand from CSV
-------------------------------------------------------------

.. automodule:: smooth.components.component_energy_demand_from_csv
   :members:
   :undoc-members:
   :show-inheritance:

Energy Source from CSV
-------------------------------------------------------------

.. automodule:: smooth.components.component_energy_source_from_csv
   :members:
   :undoc-members:
   :show-inheritance:

Fuel cell CHP
---------------------------------------------------

.. automodule:: smooth.components.component_fuel_cell_chp
   :members:
   :undoc-members:
   :show-inheritance:
   
Gas Engine CHP Biogas
------------------------------------------------------------

.. automodule:: smooth.components.component_gas_engine_chp_biogas
   :members:
   :undoc-members:
   :show-inheritance:

Gate
------------------------------------------------------------

.. automodule:: smooth.components.component_gate
   :members:
   :undoc-members:
   :show-inheritance:
   
H2 Refuel Cooling System
------------------------------------------------------------

.. automodule:: smooth.components.component_h2_refuel_cooling_system
   :members:
   :undoc-members:
   :show-inheritance:

Sink
----------------------------------------

.. automodule:: smooth.components.component_sink
   :members:
   :undoc-members:
   :show-inheritance:

Storage H2
-----------------------------------------------

.. automodule:: smooth.components.component_storage_h2
   :members:
   :undoc-members:
   :show-inheritance:

Stratified Thermal Storage
-----------------------------------------------

.. automodule:: smooth.components.component_stratified_thermal_storage
   :members:
   :undoc-members:
   :show-inheritance:

Supply
------------------------------------------

.. automodule:: smooth.components.component_supply
   :members:
   :undoc-members:
   :show-inheritance:

Trailer H2 Delivery
------------------------------------------

.. automodule:: smooth.components.component_trailer_h2_delivery
   :members:
   :undoc-members:
   :show-inheritance:

External Components
------------------------------------------

.. automodule:: smooth.components.external_component
   :members:
   :undoc-members:
   :show-inheritance:

H2 Dispenser
------------------------------------------

.. automodule:: smooth.components.external_component_h2_dispenser
   :members:
   :undoc-members:
   :show-inheritance:

