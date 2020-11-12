import oemof.solph as solph
from .component import Component


class TrailerGateCascade(Component):
    """Gate component is created to control the output flows from one trailer delivery
    to two different delivery sites"""

    def __init__(self, params):
        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------- PARAMETERS -----------------
        self.name = 'Gate_default_name'

        self.max_input = None

        # Busses
        self.bus_in = None
        self.bus_out = None

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

    def prepare_simulation(self, components):
        # Update the artificial costs for this time step (dependant on foreign states).
        if self.fs_component_name is not None:
            self.max_input = self.get_foreign_state_value(components, index=0)

    def create_oemof_model(self, busses, _):
        trailer_gate = solph.Transformer(
            label=self.name,
            inputs={busses[self.bus_in]: solph.Flow(nominal_value=self.max_input)},
            outputs={busses[self.bus_out]: solph.Flow()}
        )
        return trailer_gate
