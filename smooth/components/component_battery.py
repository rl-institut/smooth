"""
This module represents a stationary battery.

*****
Scope
*****
Batteries are crucial in effectively integrating high shares of renewable
energy electricity sources in diverse energy systems. They can be particularly
useful for off-grid energy systems, or for the management of grid stability
and flexibility. This flexibility is provided to the energy system by the
battery in times where the electric consumers cannot.

*******
Concept
*******
The battery component has an electricity bus input and output, where factors
such as the charging and discharging efficiency, the loss rate, the C-rates
and the depth of discharge define the electricity flows.

Wanted storage level
--------------------
Within this component, there is the possibility to choose a wanted
storage level that the energy system should try to maintain when it
feasibly can. If the state of charge level wanted is defined, the variable
artificial costs change depending on whether the storage level is above or
below the desired value. If the battery level is too low, the artificial
costs of storing electricity into the battery can be reduced and the costs
of extracting electricity from the battery can be increased to incentivise
the system to maintain the wanted storage level.

Maximum chargeable/dischargeable energy
---------------------------------------
The maximum chargeable and dischargeable energy [Wh] per timestep is dependant on
the C-rate and the state of charge of the battery. Because of the charging losses
defined by charging efficiency, the nominal value of the input flow must be higher
than what is actually entering the battery in order to ensure that the battery can
be fully charged in one time step. Due to the *inflow_conversion_factor*
parameter (in :func:`~smooth.components.component_battery.Battery.create_oemof_model`),
the battery will then receive the right amount.

.. math::
    E_{in,max} = \\frac{min(c_{r,charge} \\cdot C \\cdot \\frac{t}{60},
    C - SOC \\cdot C)}{\\mu_{charge}} \n
    E_{out,max} = min(c_{r,discharge} \\cdot C \\cdot \\frac{t}{60}, SOC \\cdot C)

* :math:`E_{in,max}` = maximum chargeable energy [Wh]
* :math:`c_{r,charge}` = C-Rate [-/h]
* :math:`C` = storage capacity [Wh]
* :math:`SOC` = state of charge [Wh]
* :math:`\\mu_{charge}` = charging efficiency [-]
* :math:`E_{out,max}` = maximum dischargeable energy [Wh]
* :math:`c_{r,discharge}` = C-Rate [-/h]
"""

import oemof.solph as solph
from .component import Component
from oemof.outputlib import views


class Battery(Component):
    """
    :param name: unique name given to the battery component
    :type name: str
    :param bus_in_and_out: electricity bus the battery is connected to
    :type bus_in_and_out: str
    :param battery_capacity: battery capacity (assuming all the capacity
        can be used) [Wh]
    :type battery_capacity: numerical
    :param soc_init: initial state of charge [-]
    :type soc_init: numerical
    :param efficiency_charge: charging efficiency [-]
    :type efficiency_charge: numerical
    :param efficiency_discharge: discharging efficiency [-]
    :type efficiency_discharge: numerical
    :param loss_rate: loss rate [%/day]
    :type loss_rate: numerical
    :param c_rate_charge: C-Rate [-/h]
    :type c_rate_charge: numerical
    :param c_rate_discharge: C-Rate [-/h]
    :type c_rate_discharge: numerical
    :param dod: depth of discharge [-]
    :type dod: numerical
    :param life_time: life time of the component [a]
    :type life_time: numerical
    :param vac_in: normal variable artificial costs for charging (in)
        the battery [EUR/Wh]
    :type vac_in: numerical
    :param vac_out: normal variable artificial costs for discharging (out)
        the battery [EUR/Wh]
    :type vac_out: numerical
    :param soc_wanted: if a soc level is set as wanted, the vac_low costs
        apply if the capacity is below that level [Wh]
    :type soc_wanted: numerical
    :param vac_low_in: variable artificial costs that apply (in) if the capacity
        level is below the wanted capacity level [EUR/Wh]
    :type vac_low_in: numerical
    :param vac_low_out: variable artificial costs that apply (in) if the capacity
        level is below the wanted capacity level [EUR/Wh]
    :type vac_low_out: numerical
    :param set_parameters(params): updates parameter default values
        (see generic Component class)
    :type set_parameters(params): function
    :param soc: state of charge [-]
    :type soc: numerical
    :param e_in_max: max. chargeable energy [Wh]
    :type e_in_max: numerical
    :param e_out_max: max. dischargeable energy [Wh]
    :type e_out_max: numerical
    :param loss_rate: adjusted loss rate to chosen timestep [%/timestep]
    :type loss_rate: numerical
    :param current_vac: current artificial costs for input and output [EUR/Wh]
    :type current_vac: list
    """

    def __init__(self, params):
        """Constructor method
        """
        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = "Battery_default_name"

        self.bus_in_and_out = None
        self.battery_capacity = 5000
        self.soc_init = 0.5
        # ToDo: set default value for efficiency
        self.efficiency_charge = 0.95
        self.efficiency_discharge = 0.95
        # ToDo: set default value loss rate
        self.loss_rate = None
        # ToDo: set default value for c-rate
        self.c_rate_charge = 1
        self.c_rate_discharge = 1
        # ToDo: set default value for depth of discharge
        self.dod = None
        # ToDo: set default value life time. Per cycle or time
        self.life_time = 20
        # ToDo: set default value for degradation over lifetime
        # Degradation over lifetime [%]
        # self.degradation =

        # ------------------- PARAMETERS (VARIABLE ARTIFICIAL COSTS - VAC) -------------------
        # Normal var. art. costs for charging (in) and discharging (out) the
        # battery [EUR/Wh]. vac_out should be set to a minimal value to ensure,
        # that the supply for the demand is first satisfied by the renewables
        # (costs are 0), second satisfied by the battery and last by the grid.
        self.vac_in = None
        self.vac_out = None
        self.soc_wanted = None
        self.vac_low_in = 0
        self.vac_low_out = 0

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)
        # Raise an error if the initial state of charge [%] is set below depth of discharge [%].
        if self.soc_init < self.dod:
            raise ValueError(
                'Initial state of charge is set below depth of discharge! '
                'Please adjust soc_init or dod.')

        # ------------------- STATES -------------------
        self.soc = self.soc_init
        self.e_in_max = None
        self.loss_rate = (self.loss_rate / 24) * (self.sim_params.interval_time / 60)

        # ------------------- VARIABLE ARTIFICIAL COSTS -------------------
        self.current_vac = [0, 0]

    def prepare_simulation(self, components):
        """Prepares the simulation by setting the appropriate artificial costs
        and the maximum chargeable or dischargeable energy into/out of the
        battery.

        :param components: List containing each component object
        :type components: list
        :return: artificial costs and maximum chargeable or dischargeable energy
        """
        # Set the var. art. costs.
        vac_in = self.vac_in
        vac_out = self.vac_out

        if self.soc_wanted is not None and self.soc < self.soc_wanted:
            # If a wanted storage level is set and the storage level drops
            # below that wanted level, the low VAC apply.
            vac_in = self.vac_low_in
            vac_out = self.vac_low_out

        self.current_vac = [vac_in, vac_out]

        # ToDo: efficiency depending on the soc

        # ToDo: c_rate depending on the soc

        # Max. chargeable or dischargeable energy [Wh] going in from the bus
        # due to c_rate depending on the soc. To ensure that the battery can
        # be fully charged in one timestep, the nominal value of the input-flow
        # needs to be higher than what's actually going into the battery.
        # Therefore we need to divide by the efficiency_charge.  Due to the
        # inflow_conversion_factor (in "create oemof model") the battery will
        # then receive right amount.
        self.e_in_max = min(
            self.c_rate_charge * self.battery_capacity * self.sim_params.interval_time / 60,
            self.battery_capacity - self.soc * self.battery_capacity) / \
            self.efficiency_charge
        self.e_out_max = min(
            self.c_rate_discharge * self.battery_capacity * self.sim_params.interval_time / 60,
            self.soc * self.battery_capacity)

    def create_oemof_model(self, busses, _):
        """Creates an oemof Generic Storage component from the information given in
        the Battery class, to be used in the oemof model.

        :param busses: List of the virtual buses used in the energy system
        :type busses: list
        :return: The 'battery' oemof component
        """
        battery = solph.components.GenericStorage(
            label=self.name,
            inputs={busses[self.bus_in_and_out]: solph.Flow(
                    nominal_value=self.e_in_max, variable_costs=self.current_vac[0])
                    },
            outputs={busses[self.bus_in_and_out]: solph.Flow(
                nominal_value=self.e_out_max, variable_costs=self.current_vac[1])
            },
            loss_rate=self.loss_rate,
            initial_storage_level=self.soc,
            nominal_storage_capacity=self.battery_capacity,
            min_storage_level=self.dod,
            inflow_conversion_factor=self.efficiency_charge,
            outflow_conversion_factor=self.efficiency_discharge,
            balanced=False,
        )
        return battery

    def update_states(self, results, sim_params):
        """Updates the states of the battery component for each time step

        :param results: oemof results for the given time step
        :type results: object
        :param sim_params: simulation parameters for the energy system (defined by user)
        :type sim_params: object
        :return: updated state values for each state in the 'state' dict
        """
        data_storage = views.node(results, self.name)
        df_storage = data_storage["sequences"]

        # Loop Through the data frame values and update states accordingly.
        for i_result in df_storage:
            if i_result[1] == "capacity":
                if "soc" not in self.states:
                    # Initialize a.n array that tracks the state SoC
                    self.states["soc"] = [None] * sim_params.n_intervals
                # Check if this result is the state of charge.
                self.soc = df_storage[i_result][0] / self.battery_capacity
                self.states["soc"][sim_params.i_interval] = self.soc
