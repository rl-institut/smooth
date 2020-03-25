import oemof.solph as solph
from .component import Component


class Sink(Component):
    """ Excess electricity sold to the grid is created through this class """

    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)
        """ PARAMETERS """
        self.name = 'Grid_default_name'

        # Max. power that can be taken by the sink [W]
        self.power_max = 800000000

        self.bus_in = None

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

        """ COSTS """
        # Define the costs for electricity (negative means earning money) [EUR/Wh].
        self.electricity_costs = self.get_costs_and_art_costs()

    def create_oemof_model(self, busses, _):
        sink = solph.Sink(
            label=self.name,
            inputs={busses[self.bus_in]: solph.Flow(
                variable_costs=self.electricity_costs,
                nominal_value=self.power_max
            )})
        return sink
