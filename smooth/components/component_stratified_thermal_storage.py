import oemof.solph as solph
from smooth.components.component import Component
from numpy import pi
from oemof.outputlib import views
import smooth.framework.functions.functions as func
import os


class StratifiedThermalStorage (Component):
    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = 'Stratified_thermal_storage_default_name'

        # Define the heat bus the storage is connected to.
        self.bus_in = None
        self.bus_out = None

        # Storage capacity [Wh]
        self.storage_capacity = 6000e3
        # Calculate the minimum storage level relative to storage capacity [Wh]
        self.storage_level_min = 0.025
        # Calculate the maximum storage level relative to storage capacity [Wh]
        self.storage_level_max = 0.975
        # The maximum heat charged into the storage per timestep [Wh]
        self.max_heat_flow_charge = self.storage_level_max * self.storage_capacity
        # The maximum heat discharged into the storage per timestep [Wh]
        self.max_heat_flow_discharge = (1 - self.storage_level_min) * self.storage_capacity
        # Initial USABLE storage level factor in relation to the capacity
        self.initial_storage_factor = 0.5
        # Lifetime [a]
        self.life_time = 20

        # To be used for extracting an environmental temp timeseries from csv file
        self.nominal_value = 1
        self.csv_filename = None
        self.csv_separator = ','
        self.column_title = 0
        self.path = os.path.dirname(__file__)

        # ------------------- PARAMETERS TAKEN FROM OEMOF THERMAL EXAMPLE FILE -------------------
        # Density of the storage medium [kg/m3]
        self.density = 971.78
        # Heat capacity of the storage medium [J/(kg*K)]
        self.heat_capacity = 4180
        # The hot temperature level of the stratified storage tank [K]
        self.temp_h = 368.15
        # The cold temperature level of the stratified storage tank [K]
        self.temp_c = 333.15
        # The environment temperature value [C] because timeseries is usually in degrees C
        self.temp_env = 25
        # The chosen height to diameter ratio [-]
        self.height_diameter_ratio = 3
        # Thickness of isolation layer [m]
        self.s_iso = 0.05
        # Heat conductivity of isolation material [W/(m*K)]
        self.lamb_iso = 0.03
        # Heat transfer coefficient inside [W/(m2*K)]
        self.alpha_inside = 1
        # Heat transfer coefficient outside [W/(m2*K)]
        self.alpha_outside = 1

        # ------------------- PARAMETERS (VARIABLE ARTIFICIAL COSTS - VAC) -------------------
        # Normal var. art. costs for charging (in) and discharging (out) the storage [EUR/Wh.
        self.vac_in = 0
        self.vac_out = 0
        # If a storage level is set as wanted, the vac_low costs apply if the
        # storage is below that level [Wh].
        self.storage_level_wanted = None
        # Var. art. costs that apply if the storage level is below the wanted
        # storage level [EUR/Wh].
        self.vac_low_in = 0
        self.vac_low_out = 0

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)
        self.storage_level_init = self.initial_storage_factor * self.storage_capacity

        # Check to see if the environmental temperature has been given as a
        # timeseries or a singular value
        if self.csv_filename is not None:
            # The environment temperature timeseries [K}
            self.temp_env = func.read_data_file(
                self.path, self.csv_filename, self.csv_separator, self.column_title)
            self.temp_env = self.temp_env[self.column_title].values.tolist()
            self.temp_env = [temp + 273.15 for temp in self.temp_env]

        # ------------------- STATES -------------------
        # Storage level [kg of h2]
        self.storage_level = min(self.storage_level_init +
                                 self.storage_level_min, self.storage_capacity)

        # ------------------- VARIABLE ARTIFICIAL COSTS -------------------
        # Store the current artificial costs for input and output [EUR/kg].
        self.current_vac = [0, 0]

        # -------- FURTHER STORAGE VALUES DEPENDING ON SPECIFIED PARAMETERS --------
        # Calculate the storage volume [m³].
        self.volume \
            = self.get_volume(
                self.storage_capacity, self.heat_capacity, self.density, self.temp_h, self.temp_c)
        # Calculate the diameter of the storage [m]
        self.diameter = self.get_diameter(self.volume, self.height_diameter_ratio)
        # The thermal transmittance is calculated [W/(m2*K)]
        self.u_value = self.calculate_storage_u_value(
            self.alpha_inside, self.s_iso, self.lamb_iso, self.alpha_outside)
        # The losses in the storage are precalculated based on constant
        # parameters and the environmental temperature timeseries
        [self.loss_rate, self.fixed_losses_relative, self.fixed_losses_absolute] \
            = self.calculate_losses(
            self.sim_params,
            self.u_value,
            self.diameter,
            self.density,
            self.heat_capacity,
            self.temp_c,
            self.temp_h,
            self.temp_env)

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

    def create_oemof_model(self, busses, _):
        thermal_storage = solph.components.GenericStorage(
            label=self.name,
            outputs={busses[self.bus_out]: solph.Flow(variable_costs=self.current_vac[1],
                                                      nominal_value=self.max_heat_flow_discharge)},
            inputs={busses[self.bus_in]: solph.Flow(variable_costs=self.current_vac[0],
                                                    nominal_value=self.max_heat_flow_charge)},
            initial_storage_level=self.storage_level / self.storage_capacity,
            nominal_storage_capacity=self.storage_capacity,
            min_storage_level=self.storage_level_min / self.storage_capacity,
            loss_rate=self.loss_rate,
            fixed_losses_relative=self.fixed_losses_relative[self.sim_params.i_interval],
            fixed_losses_absolute=self.fixed_losses_absolute[self.sim_params.i_interval],
            inflow_conversion_factor=1,
            outflow_conversion_factor=1,
            balanced=False)
        return thermal_storage

    def update_states(self, results, sim_params):
        data_storage = views.node(results, self.name)
        df_storage = data_storage['sequences']

        # Loop Through the data frame values and update states accordingly.
        for i_result in df_storage:
            if i_result[1] == 'capacity':
                if 'storage_level' not in self.states:
                    # Initialize an array that tracks the state stored mass.
                    self.states['storage_level'] = [None] * sim_params.n_intervals
                # Check if this result is the storage capacity.
                self.storage_level = df_storage[i_result][0]
                self.states['storage_level'][sim_params.i_interval] = self.storage_level

    def get_volume(self, s_c, h_c, de, t_h, t_c):
        volume = s_c * 3600 / (h_c * de * (t_h - t_c))
        return volume

    def get_diameter(self, V, h_d_ratio):
        diameter = ((4 * V) / (pi * h_d_ratio))**(1 / 3)
        return diameter

    def calculate_storage_u_value(self, a_in, s_iso, l_iso, a_out):
        # Function from oemof-thermal: CHECK ABOUT S_ISO UNITS
        denominator = 1 / a_in + s_iso / l_iso + 1 / a_out
        u_value = 1 / denominator
        return u_value

    def calculate_losses(self, sim_params, u_val, d, de, h_c, t_c, t_h, t_env, time_increment=1):
        loss_rate = (
            4 * u_val * 1 / (d * de * h_c) * time_increment
            * 3600  # Ws to Wh
        )

        # check to see if t_env is a single value or a timeseries
        if isinstance(t_env, int) is True or isinstance(t_env, float) is True:
            # if t_env is a single value, convert into a list
            t_env = [t_env] * sim_params.n_intervals

        fixed_losses_relative = [4 * u_val * (t_c - this_t_env)
                                 * 1 / ((d * de * h_c) * (t_h - t_c))
                                 * time_increment
                                 # multiply by 3600 to convert Ws to Wh
                                 * 3600 for this_t_env in t_env]

        fixed_losses_absolute = [
            0.25 * u_val * pi * d ** 2 * (t_h + t_c - 2 * this_t_env) * time_increment
            for this_t_env in t_env]

        return loss_rate, fixed_losses_relative, fixed_losses_absolute
