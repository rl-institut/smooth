"""
A simple electric heater component that converts electricity to heat is created through this module.

*****
Scope
*****
Electric heaters can convert electricity into heat directly with a high efficiency, which can
be useful in energy systems with large quantitites of renewable electricity production as
well as a heat demand that must be satisfied.

*******
Concept
*******
A simple oemof Transformer component is used to convert the electricity bus into
a thermal bus, with a constant efficiency of 98% applied [1].

References
----------
[1] Meyers, S. et.al. (2016). Competitive Assessment between Solar Thermal and
Photovoltaics for Industrial Process Heat Generation, International Solar
Energy Society.
"""


import oemof.solph as solph
from .component import Component


class ElectricHeater(Component):
    """
    :param name: unique name given to the electric heater component
    :type name: str
    :param bus_el: electricity bus that is the input of the electric heater
    :type bus_el: str
    :param bus_th: thermal bus that is the output of the electric heater
    :type bus_th: str
    :param power_max: maximum thermal output [W]
    :type power_max: numerical
    :param life_time: life time of the component [a]
    :type life_time: numerical
    :param efficiency: constant efficiency of the heater [-]
    :type efficiency: float (0-1)
    :param set_parameters(params): updates parameter default values (see generic Component class)
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
        self.efficiency = 0.98

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)

    def create_oemof_model(self, busses, _):
        """Creates an oemof Transformer component from the information given in the
        ElectricHeater class, to be used in the oemof model

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
