"""
A generic supply component (usually for grid supplied electricity, heat etc.) is
created through this class.

*****
Scope
*****
A supply component is a generic component that represents a supply to the energy
system such as an electricity grid or a hydrogen grid.

*******
Concept
*******
The output bus type and
the maximum output per timestep are defined by the user, and similarly to in
the sink component, the default maximum output value is set to very high to
represent a limitless capacity.

Artificial costs
----------------
There are some energy systems where the supply component should be incentivised
to be used in certain scenarios and not in others. As an example, an energy
system with renewable energy electricity production, the electricity grid as
an alternative supply and hydrogen production/storage is considered. \n

If the hydrogen storage is over a defined threshold, then the system wants to
prioritise using the stored hydrogen as an energy source instead of extracting
energy from the grid, which is achieved by setting high artificial costs on
the use of the grid component. If the hydrogen storage is below the defined
threshold, however, then the system is incentivised to use the grid so that
the storage does not entirely run out.
"""

import oemof.solph as solph
from .component import Component


class Supply (Component):
    """
    ToDo: in this component and others, change Wh etc. to either W or W * t where t is time step
    :param name: unique name given to the supply component
    :type name: str
    :param output_max: maximum output per timestep of commodity e.g. for the electricity grid [Wh],
        thermal grid [Wh], H2 grid [kg/h]
    :type output_max: numerical
    :param bus_out: output bus of the supply component e.g. the electricity bus
    :type bus_out: str
    :param fs_threshold: threshold value for artificial costs
    :type fs_threshold: numerical
    :param fs_low_art_cost: low artificial cost value e.g. [EUR/Wh], [EUR/kg]
    :type fs_low_art_cost: numerical
    :param fs_high_art_cost: high artificial cost value e.g. [EUR/Wh], [EUR/kg]
    :type fs_high_art_cost: numerical
    :param fs_pressure: pressure of the supply if required (default is None) [bar]
    :type fs_pressure: numerical
    :param set_parameters(params): updates parameter default values
        (see generic Component class)
    :type set_parameters(params): function
    :param current_ac: current artificial cost value e.g. [EUR/Wh], [EUR/kg]
    :type current_ac: numerical
    """

    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = 'Grid_default_name'
        self.output_max = 8000000
        self.bus_out = None

        # ------------- PARAMETERS ARTIFICIAL COSTS FOREIGN STATE --------------
        # The artificial costs for supplying electricity can be dependant on a
        # foreign state, like a storage SoC. Therefore the name and the state
        # name of that foreign entity have to be defined as well as the threshold
        # level, under which the low level costs are used. Above the threshold,
        # the high level artificial costs are used.

        self.fs_threshold = None
        self.fs_low_art_cost = None
        self.fs_high_art_cost = None
        self.fs_pressure = None

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)

        # ------------------- INTERNAL VALUES -------------------
        self.current_ac = 0

    def prepare_simulation(self, components):
        """Prepares the simulation by updating the artificial costs for the current
        time step (dependant on foreign states) and sets the total costs for the commodity
        for this time step (costs + artificial costs)

        :param components: List containing each component object
        :type components: list
        :return: total costs for the commodity for this time step e.g. [EUR/Wh], [EUR/kg]
        """
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
        """Creates an oemof Source component from the information given in the Supply
        class, to be used in the oemof model.

        :param busses: List of the virtual buses used in the energy system
        :type busses: list
        :return: 'from_grid' oemof component
        """
        from_grid = solph.Source(
            label=self.name,
            outputs={busses[self.bus_out]: solph.Flow(
                nominal_value=self.output_max,
                variable_costs=self.current_ac
            )})
        return from_grid
