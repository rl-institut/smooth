"""
A generic sink component (usually for excess electricity, heat etc.) is
created through this class.

*****
Scope
*****
A sink component is a virtual component that usually represents excesses
in an energy system e.g. excess electricity or heat production.

*******
Concept
*******
The sink component is generic, where the input bus type and optionally the
maximum input per time step are defined by the user. The default value is set
to very high to represent a limitless capacity.
"""

import oemof.solph as solph
from .component import Component


class Sink(Component):
    """
    :param name: unique name given to the sink component
    :type name: str
    :param input_max: maximum input per timestep of commodity e.g.
        for excess electricity [Wh], heat [Wh], hydrogen [kg]
    :type input_max: numerical
    :param bus_in: input bus of the sink component e.g. the electricity bus
    :type bus_in: str
    :param set_parameters(params): updates parameter default values
        (see generic Component class)
    :type set_parameters(params): function
    :param commodity_costs: costs for the commodities e.g. [EUR/Wh], [EUR/kg]
        (negative costs means the system earns money when the commodity enters
        the sink component)
    :type commodity_costs: numerical
    """

    def __init__(self, params):
        """Constructor method
        """
        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = 'Grid_default_name'
        self.input_max = 800000000
        self.bus_in = None

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)

        # ------------------- COSTS -------------------
        self.commodity_costs = self.get_costs_and_art_costs()

    def create_oemof_model(self, busses, _):
        """Creates an oemof Sink component from the information given in the Sink
        class, to be used in the oemof model.

        :param busses: List of the virtual buses used in the energy system
        :type busses: list
        :return: 'sink' oemof component
        """
        sink = solph.Sink(
            label=self.name,
            inputs={busses[self.bus_in]: solph.Flow(
                variable_costs=self.commodity_costs,
                nominal_value=self.input_max
            )})
        return sink
