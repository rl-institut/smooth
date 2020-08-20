"""
This module represents an air source heat pump that uses ambient air and
electricity for heat generation, based on oemof thermal's component.

*****
Scope
*****
Air source heat pumps as a means of heat generation extract outside air and
increase its temperature using a pump that requires electricity as an input.
These components have the potential for the efficient utilization of
energy production and distribution in a system, particularly in times of
high renewable electricity production coupled with a high thermal demand.

*******
Concept
*******
The basis for the air source heat pump component is obtained from the oemof
thermal component, in particular using the cmpr_hp_chiller function to
pre-calculate the coefficient of performance. For further information
on how this function works, visit oemof thermal's readthedocs site [1].

References
----------
[1] oemof thermal (2019). Compression Heat Pumps and Chillers, Read the Docs:
https://oemof-thermal.readthedocs.io/en/latest/compression_heat_pumps_and_chillers.html
"""

import os
import oemof.solph as solph
from .component import Component
import oemof.thermal.compression_heatpumps_and_chillers as cmpr_hp_chiller
import smooth.framework.functions.functions as func
import pandas as pd


class AirSourceHeatPump(Component):
    """
    :param name: unique name given to the air source heat pump component
    :type name: str
    :param bus_el: electrical bus input of the heat pump
    :type bus_el: str
    :param bus_th: thermal bus output of the heat pump
    :type bus_el: str
    :param power_max: maximum heating output [W]
    :type power_max: numerical
    :param life_time: life time of the component
    :type life_time: numerical
    :param csv_filename: csv filename containing the desired timeseries,
        e.g. 'my_filename.csv'
    :type csv_filename: str
    :param csv_separator: separator of the csv file, e.g. ',' or ';' (default is ',')
    :type csv_separator: str
    :param column_title: column title (or index) of the timeseries, default is 0
    :type column_title: str or int
    :param path: path where the timeseries csv file can be located
    :type path: str
    :param temp_threshold_icing: temperature below which icing occurs [K]
    :type temp_threshold_icing: numerical
    :param temp_threshold_icing_C: converts to degrees C for oemof thermal function [C]
    :type temp_threshold_icing_C: numerical
    :param temp_high: output temperature from the heat pump [K]
    :type temp_high: numerical
    :param temp_high_C: converts to degrees C for oemof thermal function [C]
    :type temp_high_C: numerical
    :param temp_high_C_list: converts to list for oemof thermal function
    :type temp_high_C_list: list
    :param temp_low: ambient temperature [K]
    :type temp_low: numerical
    :param temp_low_C: converts to degrees C for oemof thermal function [C]
    :type temp_low_C: numerical
    :param quality_grade: quality grade of heat pump [-]
    :type quality_grade: numerical
    :param mode: can be set to heat_pump or chiller
    :type mode: str
    :param factor_icing: COP reduction caused by icing [-]
    :type factor_icing: numerical
    :param set_parameters: updates parameter default values (see generic Component class)
    :type set_parameters(params): function
    :param cops: coefficient of performance (pre-calculated by oemof thermal function)
    :type cops: numerical
    """

    def __init__(self, params):
        """Constructor method
        """
        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = 'Heat_pump_default_name'

        self.bus_el = None
        self.bus_th = None

        # Max. heating output [W]
        self.power_max = 1000e3
        # Life time [a]
        self.life_time = 20

        self.csv_filename = None
        self.csv_separator = ','
        self.column_title = 0
        self.path = os.path.dirname(__file__)

        # ------------------- PARAMETERS BASED ON OEMOF THERMAL EXAMPLE -------------------
        # Temperature below which icing occurs [K]
        self.temp_threshold_icing = 275.15
        # Convert to degrees C for oemof_thermal function
        self.temp_threshold_icing_C = self.temp_threshold_icing - 273.15
        # The output temperature from the heat pump [K]
        self.temp_high = 313.15
        # Convert to degrees C for oemof_thermal function
        self.temp_high_C = self.temp_high - 273.15
        # Convert to a list for oemof_thermal function
        self.temp_high_C_list = [self.temp_high_C]
        # The ambient temperature [K]
        self.temp_low = 283.15
        # Convert to degrees C for oemof_thermal function
        self.temp_low_C = self.temp_low - 273.15
        # Quality grade of heat pump [-]
        self.quality_grade = 0.4
        # Can be set to heat pump or chiller
        self.mode = 'heat_pump'
        # COP reduction caused by icing [-]
        self.factor_icing = 0.8
        # Ask Jann about this/look more into detail
        # self.consider_icing = False

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)

        if self.csv_filename is not None:
            # A csv file containing data for the ambient temperature is required [deg C]
            self.temp_low = func.read_data_file(
                self.path, self.csv_filename, self.csv_separator, self.column_title)
            self.temp_low_series = self.temp_low[self.column_title]
            self.temp_low_series_C = pd.Series(self.temp_low_series - 273.15)
        else:
            self.temp_low_list = [self.temp_low_C] * self.sim_params.n_intervals
            self.temp_low_series_C = pd.Series(self.temp_low_list)

        # A function taken from oemof thermal that calculates the coefficient
        # of performance (pre-calculated)
        self.cops = cmpr_hp_chiller.calc_cops(
            self.mode,
            self.temp_high_C_list,
            self.temp_low_series_C,
            self.quality_grade,
            self.temp_threshold_icing_C,
            # self.consider_icing,
            self.factor_icing)

    def create_oemof_model(self, busses, _):
        """Creates an oemof Transformer component from information given in
        the AirSourceHeatPump class, to be used in the oemof model

        :param busses: virtual buses used in the energy system
        :type busses: list
        :return: the oemof air source heat pump component
        """
        air_source_heat_pump = solph.Transformer(
            label=self.name,
            inputs={busses[self.bus_el]: solph.Flow(variable_costs=0)},
            outputs={busses[self.bus_th]: solph.Flow(
                nominal_value=self.power_max,
                variable_costs=0)},
            conversion_factors={busses[self.bus_th]: self.cops[self.sim_params.i_interval]}
        )
        return air_source_heat_pump
