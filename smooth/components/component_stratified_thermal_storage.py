"""
This module represents a stratified thermal storage tank, based on
oemof thermal's component.

******
Scope
******
A stratified thermal storage vessel is able to store thermal energy
through stratification, and thus minimise energy wastage in systems.

*******
Concept
*******
This component has been largely based on oemof thermal's stratified
thermal storage component. Visit oemof thermal's readthedocs site for
detailed information on how the component was constructed [1].

.. figure:: /images/stratified_thermal_storage.png
    :width: 60 %
    :alt: stratified_thermal_storage.png
    :align: center

    Fig.1: Simple diagram of an electric heater.

References
----------
[1] oemof thermal (2019). Stratified thermal storage, Read the Docs:
    https://oemof-thermal.readthedocs.io/en/latest/stratified_thermal_storage.html

"""

import oemof.solph as solph
from smooth.components.component import Component
from numpy import pi
from oemof.outputlib import views
import smooth.framework.functions.functions as func
import os


class StratifiedThermalStorage (Component):
    """
    :param name: unique name given to the stratified thermal storage component
    :type name: str
    :param bus_in: thermal bus input of the storage
    :type bus_in: str
    :param bus_out: thermal bus output of the storage
    :type bus_out: str
    :param storage_capacity: storage capacity [Wh]
    :type storage_capacity: numerical
    :param storage_level_min: minimum storage level relative to storage capacity [-]
    :type storage_level_min: numerical
    :param storage_level_max: maximum storage level relative to storage capacity [-]
    :type storage_level_max: numerical
    :param max_heat_flow_charge: maximum heat charged into the storage per timestep [Wh]
    :type max_heat_flow_charge: numerical
    :param max_heat_flow_discharge: maximum heat discharged from the storage per timestep [Wh]
    :type max_heat_flow_discharge: numerical
    :param storage_level_init: initial storage level [Wh]
    :type storage_level_init: numerical
    :param life_time: lifetime of the component [a]
    :type life_time: numerical
    :param nominal_value: value that the timeseries should be multipled by, default is 1
    :type nominal_value: numerical
    :param csv_filename: csv filename containing the desired demand timeseries e.g.
    'my_demand_filename.csv'
    :type csv_filenmae: str
    :param csv_separator: separator of the csv file e.g. ',' or ';', default is ','
    :type csv_separator: str
    :param column_title: column title (or index) of the timeseries, default is 0
    :type column_title: str or int
    :param path: path where the timeseries csv file can be located
    :type path: str
    :param density: density of the storage medium [kg/m3]
    :type density: numerical
    :param heat_capacity: heat capacity of the storage medium [J/(kg*K)]
    :type heat_capacity: numerical
    :param temp_h: hot temperature level of the stratified storage tank [K]
    :type temp_h: numerical
    :param temp_c: cold temperature level of the stratified storage tank [K]
    :type temp_c: numerical
    :param temp_env: environment temperature value [C] because timeseries usually in degrees C
    :type temp_env: numerical
    :param height_diameter_ratio: height to diameter ratio of storage tank [-]
    :type height_diameter_ratio: numerical
    :param s_iso: thickness of isolation layer [m]
    :type s_iso: numerical
    :param lamb_iso: heat conductivity of isolation material [W/(m*K)]
    :type lamb_iso: numerical
    :param alpha_inside: heat transfer coefficient inside [W/(m2*K)]
    :type alpha_inside: numerical
    :param alpha_outside: heat transfer coefficient outside [W/(m2*K)]
    :type alpha_outside: numerical
    :param vac_in: normal var. art. costs for charging in the storage [EUR/Wh]
    :type vac_in: numerical
    :param vac_out: normal var. art. costs for discharging out the storage [EUR/Wh]
    :type vac_out: numerical
    :param storage_level_wanted: if a storage level is set as wanted, the vac_low costs
        apply if the storage is below that level [Wh].
    :type storage_level_wanted: numerical
    :param vac_low_in: var. art. costs that apply if storage level is below
        wanted storage level [Wh]
    :type vac_low_in: numerical
    :param vac_low_out: var. art. costs that apply if storage level is below
        wanted storage level [Wh]
    :type vac_low_out: numerical
    :param set_parameters(params): updates parameter default values
        (see generic Component class)
    :type set_parameters(params): function
    :param storage_level: storage level [Wh]
    :type storage_level: numerical
    :param current_vac: stores the current artificial costs for input and output [EUR/Wh]
    :type current_vac: array
    :param volume: storage volume [m³]
    :type volume: numerical
    :param diameter: diameter of the storage [m]
    :type diameter: numerical
    :param u_value: thermal transmittance [W/(m2*K)]
    :type u_value: numerical
    :param loss_rate: relative loss of the storage capacity between
        two consecutive timesteps [-]
    :type loss_rate: numerical (sequence or scalar)
    :param fixed_losses_relative: losses independent of state of charge between
        two consecutive timesteps relative to nominal storage capacity [-]
    :type fixed_losses_relative: numerical (sequence or scalar)
    :param fixed_losses_absolute: losses independent of state of charge and independent
        of nominal storage capacity between two consecutive timesteps [Wh]
    :type fixed_losses_absolute: numerical (sequence or scalar)
    """

    def __init__(self, params):
        """Constructor method
        """
        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = 'Stratified_thermal_storage_default_name'
        self.bus_in = None
        self.bus_out = None
        self.storage_capacity = 6000e3
        self.storage_level_min = 0.025
        self.storage_level_max = 0.975
        self.max_heat_flow_charge = self.storage_level_max * self.storage_capacity
        self.max_heat_flow_discharge = (1 - self.storage_level_min) * self.storage_capacity
        self.initial_storage_factor = 0.5
        self.life_time = 20
        self.nominal_value = 1
        self.csv_filename = None
        self.csv_separator = ','
        self.column_title = 0
        self.path = os.path.dirname(__file__)

        # ------------------- PARAMETERS TAKEN FROM OEMOF THERMAL EXAMPLE FILE -------------------
        self.density = 971.78
        self.heat_capacity = 4180
        self.temp_h = 368.15
        self.temp_c = 333.15
        self.temp_env = 25
        self.height_diameter_ratio = 3
        self.s_iso = 0.05
        self.lamb_iso = 0.03
        self.alpha_inside = 1
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
            self.u_value,
            self.diameter,
            self.density,
            self.heat_capacity,
            self.temp_c,
            self.temp_h,
            self.temp_env)

    def prepare_simulation(self, components):
        """Prepares the simulation by applying the appropriate variable artificial costs

        :param components: List containing each component object
        :type components: list
        :return: array containing var. art. costs in and out of the storage
        """
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
        """Creates an oemof GenericStorage component from the information given in the
        Stratified Thermal Storage class, to be used in the oemof model

        :param busses: virtual buses used in the energy system
        :type busses: list
        :return: the oemof thermal storage component
        """
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

    def update_states(self, results):
        """Updates the states of the thermal storage component for each time step

        :param results: oemof results for the given time step
        :type results: object
        :return: updated state values for each state in the 'state' dict
        """
        data_storage = views.node(results, self.name)
        df_storage = data_storage['sequences']

        # Loop Through the data frame values and update states accordingly.
        for i_result in df_storage:
            if i_result[1] == 'capacity':
                if 'storage_level' not in self.states:
                    # Initialize an array that tracks the state stored mass.
                    self.states['storage_level'] = [None] * self.sim_params.n_intervals
                # Check if this result is the storage capacity.
                self.storage_level = df_storage[i_result][0]
                self.states['storage_level'][self.sim_params.i_interval] = self.storage_level

    def get_volume(self, s_c, h_c, de, t_h, t_c):
        """Calculates the storage tank volume

        :param s_c: storage capacity [Wh]
        :type s_c: numerical
        :param h_c: heat capacity of storage medium [J/(kg*K)]
        :type h_c: numerical
        :param de: density of the storage medium [kg/m3]
        :type de: numerical
        :param t_h: hot temperature level of the stratified storage tank [K]
        :type t_h: numerical
        :param t_c: cold temperature level of the stratified storage tank [K]
        :type t_c: numerical
        :return: storage tank volume
        """
        volume = s_c * 3600 / (h_c * de * (t_h - t_c))
        return volume

    def get_diameter(self, V, h_d_ratio):
        """Calculates the diameter of the storage tank

        :param V: storage tank volume [m3]
        :type V: numerical
        :param h_d_ratio: height to diameter ratio of storage tank [-]
        :type h_d_ratio: numerical
        :return: storage tank diameter
        """
        diameter = ((4 * V) / (pi * h_d_ratio))**(1 / 3)
        return diameter

    def calculate_storage_u_value(self, a_in, s_iso, l_iso, a_out):
        """Calculates the u value (thermal transmittance) of storage envelope

        :param a_in: heat transfer coefficient inside [W/(m2*K)]
        :type a_in: numerical
        :param s_iso: thickness of isolation layer [m]
        :type s_iso: numerical
        :param l_iso: heat conductivity of isolation material [W/(m*K)]
        :type l_iso: numerical
        :param a_out: heat transfer coefficient outside [W/(m2*K)]
        :type a_out: numerical
        :return: u value
        """
        # Function from oemof-thermal
        denominator = 1 / a_in + s_iso / l_iso + 1 / a_out
        u_value = 1 / denominator
        return u_value

    def calculate_losses(self, u_val, d, de, h_c, t_c, t_h, t_env, time_increment=1):
        """Calculates the loss rate and the fixed losses for the stratified thermal storage

        :param u_val: thermal transmittance [W/(m2*K)]
        :type u_val: numerical
        :param d: diameter of storage tank [m]
        :type d: numerical
        :param de: density of the storage medium [kg/m3]
        :type de: numerical
        :param h_c: heat capacity of storage medium [J/(kg*K)]
        :type h_c: numerical
        :param t_c: cold temperature level of the stratified storage tank [K]
        :type t_c: numerical
        :param t_h: hot temperature level of the stratified storage tank [K]
        :type t_h: numerical
        :param t_env: environmental temperature [K]
        :type t_env: numerical (sequence or scalar)
        :param time_increment: time increment of the oemof.solph.EnergySytem [h]
        :type time_increment: numerical
        :return: loss rate, relative fixed losses and absolute fixed losses
        """
        loss_rate = (
            4 * u_val * 1 / (d * de * h_c) * time_increment
            * 3600  # Ws to Wh
        )

        # check to see if t_env is a single value or a timeseries
        if isinstance(t_env, int) is True or isinstance(t_env, float) is True:
            # if t_env is a single value, convert into a list
            t_env = [t_env] * self.sim_params.n_intervals

        fixed_losses_relative = [4 * u_val * (t_c - this_t_env)
                                 * 1 / ((d * de * h_c) * (t_h - t_c))
                                 * time_increment
                                 # multiply by 3600 to convert Ws to Wh
                                 * 3600 for this_t_env in t_env]

        fixed_losses_absolute = [
            0.25 * u_val * pi * d ** 2 * (t_h + t_c - 2 * this_t_env) * time_increment
            for this_t_env in t_env]

        return loss_rate, fixed_losses_relative, fixed_losses_absolute
