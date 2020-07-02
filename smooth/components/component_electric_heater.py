import oemof.solph as solph
from .component import Component


class ElectricHeater(Component):
    """A simple electric heater component that converts electricity to heat is created through this class.

    :param name: The unique name given to the electric heater component
    :type name: str
    :param bus_el: The electricity bus that is the input of the electric heater
    :type bus_el: str
    :param bus_th: The thermal bus that is the output of the electric heater
    :type bus_th: str
    :param power_max: The maximum thermal output [W]
    :type power_max: numerical
    :param life_time: The life time of the component [a]
    :type life_time: numerical
    :param efficiency: The constant efficiency of the heater [-]
    :type efficiency: float (0-1)
    :param set_parameters(params): Updates parameter default values (see generic Component class)
    :type set_parameters(params): function
    """
    def __init__(self, params):
        # Call the init function of th mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = 'Electric_heater_default_name'

        # Busses
        self.bus_th = None
        self.bus_el = None

        # Max. thermal output [W]
        self.power_max = 1000e3

        # Life time [a].
        self.life_time = 20

        # Overall efficiency of the heater [-]
        # Value taken from Meyers, S.et.al. 'Competitive Assessment between
        # Solar Thermal and Photovoltaics for Industrial Process Heat
        # Generation'
        self.efficiency = 0.98

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)

    def create_oemof_model(self, busses, _):
        """Creates an oemof Transformer component from the information given in the ElectricHeater class, to be used in the oemof model

        :param busses: The virtual buses used in the energy system
        :type busses: list
        """
        electric_heater = solph.Transformer(
            label=self.name,
            inputs={busses[self.bus_el]: solph.Flow()},
            outputs={busses[self.bus_th]: solph.Flow(
                nominal_value=self.power_max)},
            conversion_factors={busses[self.bus_th]: self.efficiency})

        return electric_heater
