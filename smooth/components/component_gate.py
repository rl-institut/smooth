import oemof.solph as solph
from .component import Component


class Gate(Component):
    """Gate component is created to transform individual specific buses into one general bus"""

    def __init__(self, params):
        # Call the init function of the mother class.
        Component.__init__(self)

        """ PARAMERTERS """
        self.name = 'Gate_default_name'

        self.max_input = None

        # Busses
        self.bus_in = None
        self.bus_out = None

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

    def create_oemof_model(self, busses, _):
        gate = solph.Transformer(
            label=self.name,
            inputs={busses[self.bus_in]: solph.Flow(variable_costs=self.artificial_costs,
                                                    nominal_value=self.max_input)},
            outputs={busses[self.bus_out]: solph.Flow()}
        )
        return gate
