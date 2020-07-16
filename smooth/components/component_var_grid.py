import oemof.solph as solph
from .component import Component


class VarGrid(Component):
    """ An electric grid with different connection levels can be created through this class """

    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = 'Variable_Grid_default_name'

        # Gridlevels [1,2,3,4,5,6] describe the grid connection:
        # [1] house connection, [2] lov voltage grid, [3] lov voltage local network station
        # [4] medium voltage grid, [5] medium voltage transformer station, [6] High Voltage
        # These can be associated with different output_max and capex for each level
        # default values for output_max from
        # https://www.stromnetz-hamburg.de/netzanschluss/netzanschlussanfrage/

        self.grid_level = 1

        # Maximum power output in each grid level
        # e.g. for the electricity grid [W]
        self.grid_l1_output_max = 30 * 1e3
        self.grid_l2_output_max = 100 * 1e3
        self.grid_l3_output_max = 540 * 1e3
        self.grid_l4_output_max = 1.5 * 1e6
        self.grid_l5_output_max = 12 * 1e6
        self.grid_l6_output_max = 100 * 1e6

        # Capex for each grid level (e.g grid connection costs)
        self.capex_l1 = {
            'key': ['poly'],
            'fitting_value': [[700, 0.018]],
            'dependant_value': ['output_max']}

        self.capex_l2 = {
            'key': ['poly'],
            'fitting_value': [[700, 0.018]],
            'dependant_value': ['output_max']}

        self.capex_l3 = {
            'key': ['poly'],
            'fitting_value': [[120000, 0.02]],
            'dependant_value': ['output_max']}

        self.capex_l4 = {
            'key': ['poly'],
            'fitting_value': [[500000, 0.02]],
            'dependant_value': ['output_max']}

        self.capex_l5 = {
            'key': ['poly'],
            'fitting_value': [[1000000, 0.01]],
            'dependant_value': ['output_max']}

        self.capex_l6 = {
            'key': ['poly'],
            'fitting_value': [[10000000, 0.01]],
            'dependant_value': ['output_max']}

        self.bus_out = None

        # ------------- PARAMETERS ARTIFICIAL COSTS FOREIGN STATE --------------
        # The artificial costs for supplying electricity can be dependant on a
        # foreign state, like a storage SoC. Therefore the name and the state
        # name of that foreign entity have to be defined as well as the threshold
        # level, under which the low level costs are used. Above the threshold,
        # the high level artificial costs are used.

        # Define the threshold value for the artificial costs.
        self.fs_threshold = None
        # Define the low and the high art. cost value e.g. [EUR/Wh], [EUR/kg]
        self.fs_low_art_cost = None
        self.fs_high_art_cost = None

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)
        # adjust to set level of grid and given timestep
        if self.grid_level == 1:
            # self.output_max = self.grid_l1_output_max * self.sim_params.interval_time / 60
            self.output_max = self.grid_l1_output_max
            self.capex = self.capex_l1
        elif self.grid_level == 2:
            # self.output_max = self.grid_l2_output_max * self.sim_params.interval_time / 60
            self.output_max = self.grid_l2_output_max
            self.capex = self.capex_l2
        elif self.grid_level == 3:
            # self.output_max = self.grid_l3_output_max * self.sim_params.interval_time / 60
            self.output_max = self.grid_l3_output_max
            self.capex = self.capex_l3
        elif self.grid_level == 4:
            # self.output_max = self.grid_l4_output_max * self.sim_params.interval_time / 60
            self.output_max = self.grid_l4_output_max
            self.capex = self.capex_l4
        elif self.grid_level == 5:
            # self.output_max = self.grid_l5_output_max * self.sim_params.interval_time / 60
            self.output_max = self.grid_l5_output_max
            self.capex = self.capex_l5
        elif self.grid_level == 6:
            # self.output_max = self.grid_l6_output_max * self.sim_params.interval_time / 60
            self.output_max = self.grid_l6_output_max
            self.capex = self.capex_l6

        # ------------------- INTERNAL VALUES -------------------
        # The current artificial cost value e.g. [EUR/Wh], [EUR/kg].
        self.current_ac = 0

    def prepare_simulation(self, components):
        # Update the artificial costs for this time step (dependant on foreign states).
        if self.fs_component_name is not None:
            foreign_state_value = self.get_foreign_state_value(components)
            if foreign_state_value < self.fs_threshold:
                self.artificial_costs = self.fs_low_art_cost
            else:
                self.artificial_costs = self.fs_high_art_cost

        # Set the total costs for the commodity this time step
        # (costs + art.  costs) e.g. [EUR/Wh], [EUR/kg].
        self.current_ac = self.get_costs_and_art_costs()

    def create_oemof_model(self, busses, _):
        from_grid = solph.Source(
            label=self.name,
            outputs={busses[self.bus_out]: solph.Flow(
                nominal_value=self.output_max,
                variable_costs=self.current_ac
            )})
        return from_grid
