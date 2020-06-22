import oemof.solph as solph
from .component import Component
from oemof.outputlib import views


class StorageH2 (Component):
    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = 'Storage_default_name'

        # Define the hydrogen bus the storage is connected to.
        self.bus_in = None
        self.bus_out = None
        # Min. and max. pressure [bar].
        self.p_min = 0
        self.p_max = 450
        # Storage capacity at p_max (usable storage + min storage) [kg].
        self.storage_capacity = 500
        # Life time [a].
        self.life_time = 20
        # The initial storage level as a factor of the capacity [-]
        self.initial_storage_factor = 0.5
        # If True, final and initial storage level are force to be equalized by the end,
        # TODO:
        # otherwise the cost of the initially stored hydrogen is incorporated into the final cost
        self.balanced = False
        self.equalize = False
        self.initial_storage_cost = 0
        # Max chargeable hydrogen in one time step in kg/h
        self.delta_max = None
        # The storage level wanted as a factor of the capacity
        self.slw_factor = None

        # ------------------- PARAMETERS (VARIABLE ARTIFICIAL COSTS - VAC) -------------------
        # Normal var. art. costs for charging (in) and discharging (out) the storage [EUR/kg].
        self.vac_in = 0
        self.vac_out = 0
        # Var. art. costs that apply if the storage level is below the wanted
        # storage level [EUR/kg].
        self.vac_low_in = 0
        self.vac_low_out = 0

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)
        # Initial storage level [kg].
        self.storage_level_init = self.initial_storage_factor * self.storage_capacity
        # If a storage level is set as wanted, the vac_low costs apply if the
        # storage is below that level [kg].
        if self.slw_factor is not None:
            self.storage_level_wanted = self.slw_factor * self.storage_capacity
        else:
            self.storage_level_wanted = None

        # ------------------- CONSTANTS FOR REAL GAS EQUATION -------------------
        # Critical temperature [K] and pressure [Pa], molar mass of H2
        # [kg/mol], the gas constant [J/(K*mol)].
        self.T_crit = 33.19
        self.p_crit = 13.13 * 1e5
        self.Mr = 2.016 * 1e-3
        self.R = 8.314
        # Redlich Kwong EoS - Parameters
        self.rk_a = 0.1428
        self.rk_b = 1.8208e-5

        # ----- FURTHER STORAGE VALUES DEPENDANT ON THE PRESSURE/CAPACITY -----
        # Calculate the storage volume [m³].
        self.V = self.get_volume(self.p_max, self.storage_capacity)
        # Calculate the mass at p_min, which can't be used [kg].
        self.storage_level_min = self.get_mass(self.p_min)
        # Asserts that the initial storage level must be greater than the minimum storage
        # level
        assert self.storage_level_init >= self.storage_level_min

        # ------------------- STATES -------------------
        # Storage level [kg of h2]
        self.storage_level = min(self.storage_level_init, self.storage_capacity)
        # Storage pressure [bar].
        self.pressure = self.get_pressure(self.storage_level)

        # ------------------- VARIABLE ARTIFICIAL COSTS -------------------
        # Store the current artificial costs for input and output [EUR/kg].
        self.current_vac = [0, 0]

    def prepare_simulation(self, components):
        # Set the var. art. costs.
        vac_in = self.vac_in
        vac_out = self.vac_out

        if self.storage_level_wanted is not None and self.storage_level < self.storage_level_wanted:
            # If a wanted storage level is set and the storage level fell below
            # that wanted level, the low VAC apply.
            vac_in = self.vac_low_in
            vac_out = self.vac_low_out

        self.current_vac = [vac_in, vac_out]

        # TODO: set default value if not defined
        # # max chargeable hydrogen in one time step in kg/h
        # self.delta_max = self.storage_capacity

        # Nb. or Intervals until end of simulation
        self.intervals_to_end = self.sim_params.n_intervals - self.sim_params.i_interval
        # Amount of hydrogen to attain balance to initial storage level
        self.charge_balance = self.storage_level_init - self.storage_level

        # Balance start and end of simulation storage level based on the minimum flow needed
        # If flow is needed within this time step, the flow will be fixed to this value
        self.min_out = max(0,
                           - self.charge_balance - self.delta_max * (self.intervals_to_end - 1))
        self.min_in = max(0,
                          self.charge_balance - self.delta_max * (self.intervals_to_end - 1))
        if self.balanced and (self.min_in != 0 or self.min_out != 0):
            self.equalize = True


    def create_oemof_model(self, busses, _):
        storage = solph.components.GenericStorage(
            label=self.name,
            outputs={busses[self.bus_out]: solph.Flow(
                nominal_value=self.delta_max, variable_costs=self.current_vac[1],
                actual_value=self.min_out/self.delta_max, fixed=self.equalize
            )},
            inputs={busses[self.bus_in]: solph.Flow(
                nominal_value=self.delta_max, variable_costs=self.current_vac[0],
                actual_value=self.min_in/self.delta_max, fixed=self.equalize
            )},
            initial_storage_level=self.storage_level / self.storage_capacity,
            nominal_storage_capacity=self.storage_capacity,
            min_storage_level=self.storage_level_min / self.storage_capacity,
            balanced=False)
        return storage

    def update_states(self, results, sim_params):
        data_storage = views.node(results, self.name)
        df_storage = data_storage['sequences']

        # Loop Through the data frame values and update states accordingly.
        for i_result in df_storage:
            if i_result[1] == 'capacity':
                if 'storage_level' not in self.states:
                    # Initialize an array that tracks the state stored mass.
                    self.states['storage_level'] = [None] * sim_params.n_intervals
                    self.states['pressure'] = [None] * sim_params.n_intervals
                # Check if this result is the storage capacity.
                self.storage_level = df_storage[i_result][0]
                self.states['storage_level'][sim_params.i_interval] = self.storage_level
                # Get the storage pressure [bar].
                self.pressure = self.get_pressure(self.storage_level)
                self.states['pressure'][sim_params.i_interval] = self.pressure

    def get_mass(self, p, V=None):
        # Calculate the mass of the storage at a certain pressure.
        # Parameters:
        #  p: pressure [bar].
        #  V: storage volume [m³].

        if V is None:
            V = self.V

        # If p_min is set to 0, the whole capacity should be usable, thus m will be zero as well.
        if V > 0 and p == 0:
            return 0

        # Storage temperature [K].
        T = 273.15 + 25
        # Convert pressure form bar to Pa [Pa].
        p = p * 1e5
        # The mass has to be defined in an iterative process by changing the spec. volume [m³/mol].
        v_spec = 10
        for i in range(10):
            v_spec = (
                self.R * T / (p + (self.rk_a / (T**0.5 * v_spec * (v_spec + self.rk_b))))
            ) + self.rk_b

        # Calculate the mass [kg].
        m = V * self.Mr / v_spec
        return m

    def get_volume(self, p, m):
        # Calculate the volume needed to fit a certain mass at given pressure.
        # Parameters:
        #  p: pressure [bar].
        #  m: mass [kg].

        # Storage temperature [K].
        T = 273.15 + 25
        # Convert pressure form bar to Pa [Pa].
        p = p * 1e5
        # The mass has to be defined in an iterative process by changing the spec. volume [m³/mol].
        v_spec = 10
        for i in range(10):
            v_spec = (
                self.R * T / (p + (self.rk_a / (T**0.5 * v_spec * (v_spec + self.rk_b))))
            ) + self.rk_b

        # Calculate the volume [m3]
        V = m * v_spec / self.Mr
        return V

    def get_pressure(self, m):
        # Calculate the storage pressure for a given mass.
        # Parameters:
        #  m: mass [kg].

        # Storage volume [m³].
        V = self.V
        # Storage temperature [K].
        T = 273.15 + 25
        # Calculate the storage pressure [Pa].
        p = self.R * T / (V * self.Mr / m - self.rk_b) - \
            self.rk_a / (T**0.5 * V * self.Mr / m * (V * self.Mr / m + self.rk_b))
        # Return pressure in bar [bar].
        return p / 1e5
