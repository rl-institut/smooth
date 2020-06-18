import os
import oemof.solph as solph
from .component import Component
from oemof.outputlib import views
import smooth.framework.functions.functions as func


class BatteryElectricVehicle(Component):
    """ Battery electric vehicle is created through this class """

    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = "Battery_EV_default_name"

        # Define the electric and mobility bus.
        self.bus_in_and_out = None
        self.bus_ev = None
        # Maximum flow from electric to mobility bus
        self.max_ev_flow = 5000
        self.charging_max = 2000
        # Battery capacity (assuming all the capacity can be used) [Wh].
        self.battery_capacity = 5000
        self.present_capacity = 5000
        # Initial State of charge [-].
        self.soc_init = 0.5
        # ToDo: set default value for efficiency
        # Efficiency charge [-].
        self.efficiency_charge = 0.95
        # Efficiency discharge [-].
        self.efficiency_discharge = 0.95
        # ToDo: set default value loss rate
        # Loss rate [%/day]
        self.loss_rate = None
        # ToDo: set default value for c-rate
        # C-Rate [-/h].
        self.c_rate_charge = 1
        self.c_rate_discharge = 1
        # ToDo: set default value for depth of discharge
        # Depth of discharge [-].
        self.dod = None
        # ToDo: set default value life time. Per cycle or time
        # ToDo: how can second life of battery be regarded.
        # Life time [a].
        self.life_time = 10
        # ToDo: set default value for degradation over lifetime
        # Degradation over lifetime [%]
        # self.degradation =

        # Out- and inflow from CSV
        self.csv_filename = None
        self.csv_separator = ','
        self.column_title = 0
        self.column_capacity = None
        self.path = os.path.dirname(__file__)

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

        # ------------------- READ CSV FILES -------------------
        self.data = func.read_data_file_multi(self.path, self.csv_filename,self.csv_separator,
                                              [self.column_title, self.column_capacity])

        # ------------------- STATES -------------------
        # State of charge [%]
        self.soc = self.soc_init
        self.remaining_energy = self.soc_init * self.present_capacity

        # Initialize max. chargeable or dischargeable energy [Wh].
        self.e_in_max = None

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

        # Max. chargeable or dischargeable energy [Wh] goinge in from the bus
        # due to c_rate depending on the soc. To ensure that the battery can
        # be fully charged in one timestep, the nominal value of the input-flow
        # needs to be higher than what's actually going into the battery.
        # Therefore we need to divide by the efficiency_charge.  Due to the
        # inflow_conversion_factor (in "create oemof model") the battery will
        # then receive right amount.
        self.leaving_energy = self.data.iloc[self.sim_params.i_interval].loc["ev_p_tot"]\
                              * self.battery_capacity
        self.remaining_energy = (self.soc * self.present_capacity) - self.leaving_energy
        self.present_capacity = self.data.iloc[self.sim_params.i_interval].loc["ev_cap_tot"]\
                                * self.battery_capacity
        self.soc = self.remaining_energy / self.present_capacity

        #TODO check max flow equations (as now based on changing capacity):
        self.e_in_max = min(
            self.c_rate_charge * self.present_capacity * self.sim_params.interval_time / 60,
            self.present_capacity - self.soc * self.present_capacity) / \
            self.efficiency_charge
        self.e_out_max = min(
            self.c_rate_discharge * self.present_capacity * self.sim_params.interval_time / 60,
            self.soc * self.present_capacity)


    def create_oemof_model(self, busses, model):
        """ Create oemof model """
        # TODO: create mobility bus which is connected to electricity bus via oemof.transformer
        #       => for now: mobility bus equals electricity bus
        self.bus_ev = self.bus_in_and_out

        battery = solph.components.GenericStorage(
            label=self.name,
            inputs={busses[self.bus_ev]: solph.Flow(
                    nominal_value=self.e_in_max, variable_costs=self.current_vac[0])
                    },
            outputs={busses[self.bus_ev]: solph.Flow(
                nominal_value=self.e_out_max, variable_costs=self.current_vac[1])
            },
            loss_rate=self.loss_rate,
            initial_storage_level=self.soc,
            nominal_storage_capacity=self.present_capacity,
            min_storage_level=self.dod,
            inflow_conversion_factor=self.efficiency_charge,
            outflow_conversion_factor=self.efficiency_discharge,
            balanced=False,
        )

        # add sink for leaving vehicles
        sink = solph.Sink(label="leaving_bev",
             inputs={busses[self.bus_ev]: solph.Flow(
                 nominal_value=self.battery_capacity,
                 actual_value=self.data.iloc[self.sim_params.i_interval].loc["ev_p_tot"],
                 fixed=True
             )}
        )

        # add source for returning vehicles
        # source = solph.Source(label="returning_bev",
        #        outputs={busses[self.bus_ev]: solph.Flow(nominal_value=self.battery_capacity,
        #                             actual_value=self.data.iloc[self.sim_params.i_interval],
        #                             fixed = True)})

        # Add the two components to the model.
        model.add(battery, sink)

        # self.model_transformer = transformer
        self.model_bat = battery
        self.model_sink = sink

        return None


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
                    self.states["remaining_energy"] = [None] * sim_params.n_intervals
                    self.states["present_capacity"] = [None] * sim_params.n_intervals
                # Check if this result is the state of charge.
                self.soc = df_storage[i_result][0] / self.battery_capacity
                self.states["soc"][sim_params.i_interval] = self.soc
                self.states["remaining_energy"][sim_params.i_interval] = self.remaining_energy
                self.states["present_capacity"] [sim_params.i_interval] = self.present_capacity
