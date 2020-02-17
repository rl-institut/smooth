import oemof.solph as solph
from .component import Component


class Ch4Grid (Component):
    """ Electricity supplied by the grid is created through this class """
    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)

        """ PARAMETERS """
        self.name = 'Grid_default_name'

        self.ch4_max = 800  # [kg/h]

        self.bus_out = None

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

        """ INTERNAL VALUES """
        # The current artificial cost value [EUR/Wh].
        self.current_ac = 0

        # Set the total costs for electricity this time step (costs + art. costs) [EUR/Wh].
        self.current_ac = self.get_costs_and_art_costs()

    def create_oemof_model(self, busses, _):
        from_ch4_grid = solph.Source(
            label=self.name,
            outputs={busses[self.bus_out]: solph.Flow(
                nominal_value=self.ch4_max,
                variable_costs=self.current_ac
            )})
        return from_ch4_grid

    def update_costs(self, results, sim_params):
        # Get the name of the flow of this component.
        flow_name = list(self.flows)
        # Get the amount of energy supplied by the grid this interval time step [Wh].
        this_ch4_supplied = self.flows[flow_name[0]][sim_params.i_interval]
        # Call the function of the mother component to save costs and art. costs for this run.
        Component.update_costs(self, results, sim_params, this_ch4_supplied)






