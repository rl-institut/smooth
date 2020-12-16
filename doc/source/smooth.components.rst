smooth.components package
=========================

This section first explains how to create a new component and what are their generic 
properties. Listed below are components that can already be used in an energy system
model (see `examples directory <https://github.com/rl-institut/smooth/tree/dev/smooth/examples>`_ 
for the usage of components in an energy system).

Building a component
--------------------
In order to build a component, you must do the following:

#. Create a subclass of the mother Component (or External Component) class. 

#. In the :func:`__init__` function, define all parameters that are specific to your component, and set default values.

#. Consider if the component requires variable artificial costs depending on system behaviour. If it does, the method for setting the appropriate costs has to be defined in the :func:`prepare_simulation` function of the new component. 

#. Define any other functions that are specific to your component.

#. All components built in SMOOTH must be created as oemof components to be used in the oemof model (see `oemof-solph's component list <https://oemof-solph.readthedocs.io/en/latest/usage.html#solph-components>`_ to choose the best fitting component). Then create the oemof component in the :func:`create_oemof_model` function, defining all of the necessary parameters.

#. If the states of the component need updating after each time step, specifiy these in the :func:`update_states` function. 

Artificial costs
----------------
The oemof framework always solves the system by minimizing the costs. In order to be able to control the system behaviour in a certain way,
artificial costs as a concept is introduced. These costs are defined in the components and are used in the oemof model (and therefore
have an effect on the cost minimization). While artificial costs are treated the same way as real costs by the oemof solver, they are
being neglected in the financial evaluation at the end of the simulation. Unwanted system behaviour can be avoided by setting high (more positive) 
artificial costs, while the solver can be incentivised to choose a desired system behaviour by implementing lower (more negative) artificial costs. 

Foreign states
--------------
Some component behaviour is dependant on so called foreign states - namely a state or attribute of another component (e.g. the 
artificial costs of the electricity grid can be dependant on a storage state of charge in order to fill the storage with grid 
electricity when the storage is below a certain threshold). While the effect of the foreign states is determined in the component itself, 
the mechanics on how to define the foreign states is the same for each component. Foreign states are always defined by the attributes:

* *fs_component_name*: string (or list of strings for multiple foreign states) of the foreign component
* *fs_attribute_name*: string (or list of strings for multiple foreign states) of the attribute name of the component

If a fixed value should be used as a foreign state, here *fs_component_name* has to be set to None and *fs_attribute_name* has to be
set to the numerical value.

Financials
----------
The costs and revenues are tracked for each component individually. There are three types of costs that are taken into 
consideration in the energy system, namely capital expenditures (CAPEX), operational expenditures (OPEX) and variable
costs. The CAPEX costs are fixed initial investment costs (EUR), the OPEX costs are the yearly operational and
maintenance costs (EUR/a) and the variable costs are those that are dependant on the use of the component in the 
system, such as the cost of buying/selling electricity from/to the grid (EUR/unit).

The ﬁnancial analysis is based on annuities of the system. The CAPEX cost of a component for one year is calculated 
by taking into consideration both the lifetime of the given component and the interest rate, and the OPEX costs remains 
the same because they are already as annuities. The variable cost annuities for the components are calculated by 
converting the summed variable costs over the simulation time to the summed variable costs over a one year period. 
If the simulation time is a year, the variable cost annuities are simply the summed variable costs for a year. The
below equations demonstrate how the CAPEX and variable costs are calculated. For more information on the financial
analysis and the possible fitting methods for the costs, refer to the update_annuities and update_fitted_cost modules in 
the :ref:`smooth.framework.functions package`.

.. math::
	CAPEX_{annuity} = CAPEX \cdot \frac{I \cdot (1 + I)^L}{(1 + I)^L -1} 

.. math::	
	VC_{annuity} = \sum VC \cdot \frac{365}{S}
	
* :math:`CAPEX_{annuity}` = CAPEX annuity [EUR/a]
* :math:`CAPEX` = total CAPEX [EUR]
* :math:`I` = interest rate [-]
* :math:`L` = component life time [a]
* :math:`VC_{annuity}` = annual variable costs [EUR/a]
* :math:`VC` = total variable costs [EUR]
* :math:`S` = number of simulation days [days]

Component - The mother class of all components
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

PEM Electrolyzer
------------------------------------------------------------

.. automodule:: smooth.components.component_pem_electrolyzer
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
   
Trailer Gate
------------------------------------------

.. automodule:: smooth.components.component_trailer_gate
   :members:
   :undoc-members:
   :show-inheritance:
   
Trailer Gate Cascade
------------------------------------------

.. automodule:: smooth.components.component_trailer_gate_cascade
   :members:
   :undoc-members:
   :show-inheritance:

Trailer H2 Delivery
------------------------------------------

.. automodule:: smooth.components.component_trailer_h2_delivery
   :members:
   :undoc-members:
   :show-inheritance:
   
Trailer H2 Delivery Cascade
------------------------------------------

.. automodule:: smooth.components.component_trailer_h2_delivery_cascade
   :members:
   :undoc-members:
   :show-inheritance:
   
Trailer H2 Delivery Single
------------------------------------------

.. automodule:: smooth.components.component_trailer_h2_delivery_single
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

Submodules
----------

Module contents
---------------

.. automodule:: smooth.components
   :members:
   :undoc-members:
   :show-inheritance:
