import sys

import oemof.solph as solph
from .component import Component
from oemof.outputlib import views


class Battery(Component):
    """ Stationary battery is created through this class """

    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)

        """ PARAMETERS """
        self.name = "Battery_default_name"

        # Define the electric bus the battery is connected to.
        self.bus_in_and_out = None
        # Battery capacity (assuming all the capacity can be used) [Wh].
        self.battery_capacity = 50000
        # Initial State of charge [%].
        self.soc_init = 0.5
        # Efficiency charge [%].
        self.efficiency_charge = 0.95
        # Efficiency discharge [%].
        self.efficiency_discharge = 0.95
        # Loss rate [%/timestep]
        self.loss_rate = 0.001
        # C-Rate [1/h].
        self.c_rate = 0.5

        # Depth of discharge [%].
        self.dod = 0.2
        # Life time [a].
        self.life_time = 20
        # ToDo: Export Error Message, if soc_init<dod
        # if self.soc_init < self.dod:
        # raise ValueError('Initial state of charge is set below depth of discharge! Please adjust soc_init.')

        """ PARAMETERS (VARIABLE ARTIFICIAL COSTS - VAC) """
        # Normal var. art. costs for charging (in) and discharging (out) the battery [EUR/Wh].
        self.vac_in = 0
        self.vac_out = 0
        # If a soc level is set as wanted, the vac_low costs apply if the capacity is below that level [Wh].
        self.soc_wanted = None
        # Var. art. costs that apply if the capacity level is below the wanted capacity level [EUR/Wh].
        self.vac_low_in = 0
        self.vac_low_out = 0

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

        # self.interval_time = self.sim_params.interval_time
        # Max. chargeable or dischargeable energy [Wh] due to c_rate.
        self.e_max = (self.c_rate * self.battery_capacity * self.sim_params.interval_time / 60)

        """ STATES """
        # State of charge [%]
        self.soc_kWh = self.soc_init * self.battery_capacity

        """ VARIABLE ARTIFICIAL COSTS """
        # Store the current artificial costs for input and output [EUR/Wh].
        self.current_vac = [0, 0]

    def prepare_simulation(self, components):
        """ Prepare simulation """
        # Set the var. art. costs.
        vac_in = self.vac_in
        vac_out = self.vac_out
        soc = self.soc_kWh / self.battery_capacity

        if self.soc_wanted is not None and soc < self.soc_wanted:
            # If a wanted storage level is set and the storage level fell below that wanted level, the low VAC apply.
            vac_in = self.vac_low_in
            vac_out = self.vac_low_out

        self.current_vac = [vac_in, vac_out]

    def create_oemof_model(self, busses, _):
        """ Create oemof model """
        storage = solph.components.GenericStorage(
            label=self.name,
            outputs={
                busses[self.bus_in_and_out]: solph.Flow(
                    nominal_value=self.e_max, variable_costs=self.current_vac[1])
            },
            inputs={
                busses[self.bus_in_and_out]: solph.Flow(
                    nominal_value=self.e_max, variable_costs=self.current_vac[0])
            },
            loss_rate=self.loss_rate,
            initial_storage_level=self.soc_kWh / self.battery_capacity,
            nominal_storage_capacity=self.battery_capacity,
            min_storage_level=self.dod,
            inflow_conversion_factor=self.efficiency_charge, outflow_conversion_factor=self.efficiency_discharge,
            balanced=False,
        )
        return storage

    def update_states(self, results, sim_params):
        """ Update states """
        data_storage = views.node(results, self.name)
        df_storage = data_storage["sequences"]

        # Loop Through the data frame values and update states accordingly.
        for i_result in df_storage:
            if i_result[1] == "capacity":
                if "soc_kWh" not in self.states:
                    # Initialize a.n array that tracks the state SoC
                    self.states["soc_kWh"] = [None] * sim_params.n_intervals
                # Check if this result is the state of charge.
                self.soc_kWh = df_storage[i_result][0]
                self.states["soc_kWh"][sim_params.i_interval] = self.soc_kWh
