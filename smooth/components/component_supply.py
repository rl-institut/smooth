import oemof.solph as solph
from .component import Component


class Supply (Component):
    """ Electricity supplied by the grid is created through this class """
    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)

        """ PARAMETERS """
        self.name = 'Grid_default_name'

        self.power_max = 8000000

        self.bus_out = None

        """ PARAMETERS ARTIFICIAL COSTS FOREIGN STATE
        The artificial costs for supplying electricity can be dependant on a foreign state, like a storage SoC. 
        Therefore the name and the state name of that foreign entity have to be defined as well as the threshold level, 
        under which the low level costs are used. Above the threshold, the high level artificial costs are used.
        """

        # Define the threshold value for the artificial costs.
        self.fs_threshold = None
        # Define the low and the high art. cost value [EUR/Wh]
        self.fs_low_art_cost = None
        self.fs_high_art_cost = None

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

        """ INTERNAL VALUES """
        # The current artificial cost value [EUR/Wh].
        self.current_ac = 0

    def prepare_simulation(self, components):
        # Update the artificial costs for this time step (dependant on foreign states).
        if self.fs_component_name is not None:
            foreign_state_value = self.get_foreign_state_value(components)
            if foreign_state_value < self.fs_threshold:
                self.variable_artificial_costs = self.fs_low_art_cost
            else:
                self.variable_artificial_costs = self.fs_high_art_cost

        # Set the total costs for electricity this time step (costs + art. costs) [EUR/Wh].
        self.current_ac = self.get_costs_and_art_costs()

    def create_oemof_model(self, busses, sim_params):
        from_grid = solph.Source(
            label=self.name,
            outputs={busses[self.bus_out]: solph.Flow(
                nominal_value=self.power_max,
                variable_costs=self.current_ac
            )})
        return from_grid

    def update_costs(self, results, sim_params):
        # Get the name of the flow of this component.
        flow_name = list(self.flows)
        # Get the amount of energy supplied by the grid this interval time step [Wh].
        this_energy_supplied = self.flows[flow_name[0]][sim_params.i_interval]
        # Call the function of the mother component to save costs and art. costs for this run.
        Component.update_costs(self, results, sim_params, this_energy_supplied)






