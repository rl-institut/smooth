import oemof.solph as solph
from .component import Component
from oemof.outputlib import views
import os
import smooth.framework.functions.functions as func
from math import pi

from oemof.thermal.stratified_thermal_storage import (
    calculate_storage_u_value,
    calculate_storage_dimensions,
    calculate_capacities,
    calculate_losses,
)


class StratifiedThermalStorage (Component):
    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)

        """ PARAMETERS """
        self.name = 'Stratified_thermal_storage_default_name'

        # Define the heat bus the storage is connected to.
        self.bus_in_and_out = None

        # Storage volume [m3]
        self.storage_volume = None
        # Initial USABLE storage level [Wh??].
        self.storage_level_init = 200
        # Life time [a].
        self.life_time = 20

        """PARAMETERS TAKEN FROM OEMOF THERMAL EXAMPLE CSV FILE"""
        # Density of the storage medium [kg/m3]
        self.density = 971.78
        # Heat capacity of the storage medium [J/(kg*K)]
        self.heat_capacity = 4180
        # The hot temperature level [deg C] MAYBE CHANGE TO KELVIN?
        self.temp_h = 95
        # The cold temperature level [deg C] MAYBE CHANGE TO KELVIN?
        self.temp_c = 60
        # The environment temperature timeseries [deg C] MAYBE CHANGE TO KELVIN?
        self.temp_env = 10
        # The charging efficiency [-]
        self.inflow_conversion_factor = 0.9
        # The discharging efficiency [-]
        self.outflow_conversion_factor = 0.9
        # Factor describing the proportion of the storage that is non-usable [-]
        self.nonusable_storage_volume = 0.05
        # Thickness of isolation layer [m]
        self.s_iso = 0.05
        # Heat conductivity of isolation material [W/(m*K)]
        self.lamb_iso = 0.03
        # Heat transfer coefficient inside [W/(m*K)]
        self.alpha_inside = 1
        # Heat transfer coefficient outside [W/(m*K)]
        self.alpha_outside = 1

        # Ratio of diameter to height [-]
        self.diameter_height_ratio = 3
        # Calculate the diameter of the storage from the storage volume and the defined diameter/height ratio [m]
        self.diameter = ((4*self.storage_volume)/(pi*self.diameter_height_ratio))**(1/3)
        # Height of storage [m]
        self.height = self.diameter * self.diameter_height_ratio

        """ PARAMETERS (VARIABLE ARTIFICIAL COSTS - VAC) """
        # Normal var. art. costs for charging (in) and discharging (out) the storage [EUR/kg].
        self.vac_in = 0
        self.vac_out = 0
        # If a storage level is set as wanted, the vac_low costs apply if the storage is below that level [kg].
        self.storage_level_wanted = None
        # Var. art. costs that apply if the storage level is below the wanted storage level [EUR/kg].
        self.vac_low_in = 0
        self.vac_low_out = 0

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

        # the thermal transmittance is calculated [W/(m2*K)]
        self.u_value = calculate_storage_u_value(self.s_iso, self.lamb_iso, self.alpha_inside, self.alpha_outside)

        # the capacities are calculated [MWh]
        [self.storage_capacity, self.storage_level_max, self.storage_level_min]\
            = calculate_capacities(self.storage_volume, self.temp_h, self.temp_c, self.nonusable_storage_volume,
                                 self.heat_capacity, self.density)

        [self.loss_rate, self.fixed_losses_relative, self.fixed_losses_absolute] \
            = calculate_losses(self.u_value, self.diameter, self.temp_h, self.temp_c, self.temp_env)

        """ STATES """
        # Storage level [kg of h2]
        self.storage_level = min(self.storage_level_init + self.storage_level_min, self.storage_capacity)

        """ VARIABLE ARTIFICIAL COSTS """
        # Store the current artificial costs for input and output [EUR/kg].
        self.current_vac = [0, 0]

    def create_oemof_model(self, busses, _):
        thermal_storage = solph.components.GenericStorage(
            label=self.name,
            outputs={busses[self.bus_in_and_out]: solph.Flow(variable_costs=self.current_vac[1])},
            inputs={busses[self.bus_in_and_out]: solph.Flow(variable_costs=self.current_vac[0])},
            initial_storage_level=self.storage_level / self.storage_capacity,
            nominal_storage_capacity=self.storage_capacity,
            min_storage_level=self.storage_level_min / self.storage_capacity,
            loss_rate=self.loss_rate,
            fixed_losses_relative=self.fixed_losses_relative,
            fixed_losses_absolute=self.fixed_losses_absolute,
            inflow_conversion_factor=1,
            outflow_conversion_factor=1,
            balanced=False)
        return thermal_storage