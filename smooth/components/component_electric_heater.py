import oemof.solph as solph
from .component import Component


class ElectricHeater(Component):
    def __init__(self, params):
        # Call the init function of th mother class.
        Component.__init__(self)

        """ PARAMETERS """
        self.name = 'Electric_heater_default_name'

        # Busses
        self.bus_th = None
        self.bus_el = None

        # Max. thermal output [W]
        self.power_max = 1000e3

        # Life time [a].
        self.life_time = 20

        # Overall efficiency of the heater [-]
        # Value taken from Meyers, S.et.al. 'Competitive Assessment between Solar Thermal and Photovoltaics for Industrial Process Heat Generation'
        self.efficiency = 0.98

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

    def create_oemof_model(self, busses, _):
        electric_heater = solph.Transformer(
            label=self.name,
            inputs={busses[self.bus_el]: solph.Flow()},
            outputs={busses[self.bus_th]: solph.Flow(
                nominal_value=self.power_max)},
            conversion_factors={busses[self.bus_th]: self.efficiency})

        return electric_heater