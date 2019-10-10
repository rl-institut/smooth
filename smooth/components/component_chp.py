import oemof.solph as solph
from .component import Component
from oemof.outputlib import views


class Chp (Component):
    """ CHP agents are created through this class """
    def __init__(self, params):
        # Call the init function of the mother class.
        Component.__init__(self)

        """ PARAMETERS """
        self.name = 'CHP_default_name'

        self.h2_energy_density = 33.3
        self.electrical_efficiency = 0.35
        self.thermal_efficiency = 0.8
        self.overall_efficiency = 0.9
        # self.annual_operating_time = 5000
        self.electricity_output_max = 3000000000 * 20 # unit is [W]
        self.thermal_output_max = 5000000000 * 20 # unit is [W]
        self.artificial_costs = None

        self.bus_h2 = None
        self.bus_el = None
        self.bus_th = None

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

        """ STATES """

    def create_oemof_model(self, busses):
        chp = solph.Transformer(
            label=self.name,
            inputs={busses[self.bus_h2]: solph.Flow()},
            outputs={busses[self.bus_el]: solph.Flow(nominal_value=self.electricity_output_max),
                     busses[self.bus_th]: solph.Flow(nominal_value=self.thermal_output_max)},
            conversion_factors={busses[self.bus_el]: self.electrical_efficiency*self.h2_energy_density*1000,
                                busses[self.bus_th]: self.thermal_efficiency*self.h2_energy_density*1000})
        return chp

