from smooth.components.component_supply import Supply


class VarGridV2(Supply):
    """ An electric grid with different connection types can be created through this class

        Gridtypes describe the grid connection, for example:
        [1] house connection, [2] lov voltage grid, [3] lov voltage local network station
        [4] medium voltage grid, [5] medium voltage transformer station, [6] High Voltage.
        Each type has to be associated with specific output_max, variable costs, capex and opex.

    :param self.name: unique name of the component
    :type self.name: str

    :param self.grid_type: set the grid type to be used
    :type self.grid_type: dict

    :param self.output_max_grid_types: Maximum power output of specific grid type [W]
    :type self.output_max_grid_types: dict

    :param self.capex_grid_types: Capex for each grid type
    :type self.capex_grid_types: dict

    :param self.opex_grid_types: Opex for each grid type
    :type self.opex_grid_types: dict

    :param self.variable_costs_grid_types: Variable costs for each grid type
    :type self.variable_costs_grid_types: dict
    """

    def __init__(self, params):
        # ------------------- PARAMETERS -------------------
        # Gridtypes [1,2,3,4,5,6] describe the grid connection:
        # [1] house connection, [2] lov voltage grid, [3] lov voltage local network station
        # [4] medium voltage grid, [5] medium voltage transformer station, [6] High Voltage
        # These can be associated with different output_max and capex for each type
        # default values for output_max from
        # https://www.stromnetz-hamburg.de/netzanschluss/netzanschlussanfrage/

        # todo: VarGridV2 als Dicts mit variablenzipieren

        # self.grid_type = 1
        self.grid_type = None

        # Maximum power output in each grid type
        # e.g. for the electricity grid [W]
        self.output_max_grid_types = {
            # 1: 30 * 1e3,
            # 2: 30 * 1e3,
            }

        # Capex for each grid type (e.g grid connection costs)
        self.capex_grid_types = {
            # 1: {
            #     'key': ['poly'],
            #     'fitting_value': [[700, 0.018]],
            #     'dependant_value': ['output_max']
            #     },
            # 2: {
            #     'key': ['poly'],
            #     'fitting_value': [[120000, 0.02]],
            #     'dependant_value': ['output_max']
            #     },
        }

        # Opex for each grid type
        self.opex_grid_types = {
            # 1: {
            #     'key': ['poly'],
            #     'fitting_value': [[700, 0.018]],
            #     'dependant_value': ['output_max'],
            # },
            # 2: {
            #     'key': ['poly'],
            #     'fitting_value': [[120000, 0.02]],
            #     'dependant_value': ['output_max'],
            # },
        }

        # Variable costs in each grid type
        # e.g. for the electricity grid [€/kW]
        self.variable_costs_grid_types = {
            # 1: 0.14 + 0.029,
            # 2: 0.14 + 0.022,
        }

        # Extract params unique in child class (VarGrid) from params and call
        # mother class (Supply) init with the general supply params
        params_child = {}
        for key in self.__dict__.keys():
            if key in params:
                params_child[key] = params.pop(key)

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        Supply.__init__(self, params)  # initialize and update "supply" parameters
        self.set_parameters(params_child)  # update parameters unique to "VarGrid"

        # validation of model

        assert self.output_max_grid_types.keys() == \
               self.capex_grid_types.keys() == \
               self.opex_grid_types.keys() == \
               self.variable_costs_grid_types.keys(), \
            'Values have to be defined for the same grid types in the same order for: ' \
            'output_max_grid_types, capex_grid_types, opex_grid_types, variable_costs_grid_types'

        assert self.grid_type in self.output_max_grid_types.keys(), \
            'The specified grid_type is not defined as key in the model definition'

        # adjust to set type of grid and given timestep
        self.output_max = self.output_max_grid_types[self.grid_type]
        self.capex = self.capex_grid_types[self.grid_type]
        self.opex = self.opex_grid_types[self.grid_type]
        self.variable_costs = self.variable_costs_grid_types[self.grid_type]
