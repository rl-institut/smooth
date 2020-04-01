import oemof.solph as solph
from .component import Component
import pandas as pd


class AirSourceHeatPump(Component):
    """ An air source heat pump component is created through this class """

    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)
        """ PARAMETERS """
        self.name = 'Heat_pump_default_name'

        self.bus_el = None
        self.bus_th = None
        # Max. power [W]
        self.power_max = 1000e3

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

        """ PARAMETERS BASED ON OEMOF THERMAL EXAMPLE """
        # Temperature below which icing occurs [degrees C] CHANGE TO KELVIN?
        self.temp_threshold_icing = 2
        # CHECK THIS
        self.temp_high = [40]
        # FIGURE OUT HOW TO DO THIS
        self.temp_low = None
        # Quality grade of heat pump [-]
        self.quality_grade = 0.4
        # DO I NEED self.mode = 'heat_pump'??
        # COP reduction caused by icing [-]
        self.factor_icing = 0.8

    def calc_cops(self, t_high, t_low, q_grad, t_t_ice, f_ice):
        # Function taken from oemof-thermal: calculates the Coefficient of Performance (COP) of heat pumps
        # based on the Carnot efficiency (ideal process) and a scale down factor

        # Check if input arguments have proper type and length
        if not isinstance(t_low, (list, pd.Series)):
            raise TypeError("Argument 'temp_low' is not of type list or pd.Series!")

        return

    def create_oemof_model(self, busses, _):
        sink = solph.Sink(
            label=self.name,
            inputs={busses[self.bus_in]: solph.Flow(
                variable_costs=self.electricity_costs,
                nominal_value=self.power_max
            )})
        return sink