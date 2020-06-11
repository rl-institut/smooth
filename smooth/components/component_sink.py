import oemof.solph as solph
from .component import Component


class Sink(Component):
    """ Generic sink component (usually for excess electricity, heat etc.) is
    created through this class """

    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)
        # ------------------- PARAMETERS -------------------
        self.name = 'Grid_default_name'

        # Maximum input per timestep of commodity:
        # e.g. for the electricity grid [Wh], thermal grid [Wh], CH4 grid [Wh]
        self.input_max = 800000000

        self.bus_in = None

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)

        # ------------------- COSTS -------------------
        # Define the costs for the commodities (negative means earning money)
        # e.g. [EUR/Wh], [EUR/kg].
        self.commodity_costs = self.get_costs_and_art_costs()

    def create_oemof_model(self, busses, _):
        sink = solph.Sink(
            label=self.name,
            inputs={busses[self.bus_in]: solph.Flow(
                variable_costs=self.commodity_costs,
                nominal_value=self.input_max
            )})
        return sink
