import oemof.solph as solph
from .component import Component
from oemof.outputlib import views


class Battery(Component):
    """ Stationary battery is created through this class """

    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = "Battery_default_name"

        # Define the electric bus the battery is connected to.
        self.bus_in_and_out = None
        # Battery capacity (assuming all the capacity can be used) [Wh].
        self.battery_capacity = 5000
        # Initial State of charge [-].
        self.soc_init = 0.5
        # Efficiency charge [-].
        self.efficiency_charge = 0.95
        # Efficiency discharge [-].
        self.efficiency_discharge = 0.95
        # Loss rate [%/day]
        self.loss_rate = 0
        # C-Rate [-/h].
        # If [symm_c_rate = True]: c_rate_symm is used for both c_rate_charge and c_rate_discharge
        self.symm_c_rate = False
        self.c_rate_symm = 1
        self.c_rate_charge = 1
        self.c_rate_discharge = 1
        # Depth of discharge [-].
        self.dod = 0
        # Life time [a].
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
        # If a soc level is set as wanted, the vac_low costs apply if the
        # capacity is below that level [Wh].
        self.soc_wanted = None
        # Var. art. costs that apply if the capacity level is below the wanted
        # capacity level [EUR/Wh].
        self.vac_low_in = 0
        self.vac_low_out = 0

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)
        # Raise an error if the initial state of charge [%] is set below depth of discharge [%].
        if self.soc_init < self.dod:
            raise ValueError(
                'Initial state of charge is set below depth of discharge! '
                'Please adjust soc_init or dod.')
        if self.symm_c_rate:
            self.c_rate_charge = self.c_rate_symm
            self.c_rate_discharge = self.c_rate_symm

        # ------------------- STATES -------------------
        # State of charge [%]
        self.soc = self.soc_init

        # Initialize max. chargeable or dischargeable power [W].
        self.p_in_max = None
        self.p_out_max = None

        # Adjust loss rate to chosen timestep [%/timestep].
        self.loss_rate = (self.loss_rate / 24) * (self.sim_params.interval_time / 60)

        # ------------------- VARIABLE ARTIFICIAL COSTS -------------------
        # Store the current artificial costs for input and output [EUR/Wh].
        self.current_vac = [0, 0]

    def prepare_simulation(self, components):
        """ Prepare simulation """
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

        # Max. chargeable or dischargeable power [W] coming in from the bus
        # depending on the c_rate [W/Wh] and the capacity [Wh].

        self.p_in_max = self.c_rate_charge * self.battery_capacity
        self.p_out_max = self.c_rate_discharge * self.battery_capacity

    def create_oemof_model(self, busses, _):
        """ Create oemof model """
        storage = solph.components.GenericStorage(
            label=self.name,
            inputs={busses[self.bus_in_and_out]: solph.Flow(
                nonconvex=solph.NonConvex(), exclusive_flow=True,
                nominal_value=self.p_in_max, variable_costs=self.current_vac[0]),
            },
            outputs={busses[self.bus_in_and_out]: solph.Flow(
                nonconvex=solph.NonConvex(), exclusive_flow=False,
                nominal_value=self.p_out_max, variable_costs=self.current_vac[1])
            },
            loss_rate=self.loss_rate,
            initial_storage_level=self.soc,
            nominal_storage_capacity=self.battery_capacity,
            min_storage_level=self.dod,
            inflow_conversion_factor=self.efficiency_charge,
            outflow_conversion_factor=self.efficiency_discharge,
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
                if "soc" not in self.states:
                    # Initialize a.n array that tracks the state SoC
                    self.states["soc"] = [None] * sim_params.n_intervals
                # Check if this result is the state of charge.
                self.soc = (df_storage[i_result][0]+0.005) / self.battery_capacity
                self.states["soc"][sim_params.i_interval] = self.soc
