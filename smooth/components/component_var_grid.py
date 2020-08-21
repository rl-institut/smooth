from smooth.components.component_supply import Supply


class VarGrid(Supply):
    """ An electric grid with different connection levels can be created through this class

        Gridlevels [1,2,3,4,5,6] describe the grid connection, if left unmodified these are:
        [1] house connection, [2] lov voltage grid, [3] lov voltage local network station
        [4] medium voltage grid, [5] medium voltage transformer station, [6] High Voltage.
        These can be associated with different output_max and capex for each level.

    :param self.name: unique name of the component
    :type self.name: str

    :param self.grid_level: set the grid level to be used
    :type self.grid_level: int (1-6)

    :param self.grid_l1_output_max: Maximum power output of specific grid level [W]
    :type self.grid_l1_output_max: int

    :param self.capex_l1: Capex for each grid level (e.g grid connection costs
    :type self.capex_l1: dict

    """

    def __init__(self, params):
        # ------------------- PARAMETERS -------------------
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

        # Extract params unique in child class (VarGrid) from params and call
        # mother class (Supply) init with the general supply params
        params_child = {}
        for key in self.__dict__.keys():
            if key in params:
                params_child[key] = params.pop(key)

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        Supply.__init__(self, params)  # initialize and update "supply" parameters
        self.set_parameters(params_child)  # update parameters unique to "VarGrid"

        # adjust to set level of grid and given timestep
        if self.grid_level == 1:
            self.output_max = self.grid_l1_output_max
            self.capex = self.capex_l1
        elif self.grid_level == 2:
            self.output_max = self.grid_l2_output_max
            self.capex = self.capex_l2
        elif self.grid_level == 3:
            self.output_max = self.grid_l3_output_max
            self.capex = self.capex_l3
        elif self.grid_level == 4:
            self.output_max = self.grid_l4_output_max
            self.capex = self.capex_l4
        elif self.grid_level == 5:
            self.output_max = self.grid_l5_output_max
            self.capex = self.capex_l5
        elif self.grid_level == 6:
            self.output_max = self.grid_l6_output_max
            self.capex = self.capex_l6
