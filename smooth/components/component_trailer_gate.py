"""
A trailer gate component is created to limit the flows into the trailer
component depending on whether delivery is possible or not.

*****
Scope
*****
The trailer gate component is a virtual component, so would not be found
in a real life energy system, but is used in parallel with the trailer
components to restrict the flows into the trailers depending on if
delivery is possible or not.

*******
Concept
*******
A transformer component is used with a hydrogen bus input and a
hydrogen bus output, where the hydrogen bus input comes from e.g.
the production site and the hydrogen bus output goes to the trailer.
The flow of hydrogen allowed to enter the trailer is controlled by
the flow switch and whether delivery is possible in the given timestep
or not.
"""


import oemof.solph as solph
from .component import Component


class TrailerGate(Component):
    """
    :param name: unique name given to the trailer gate component
    :type name: str
    :param max_input: maximum mass of hydrogen that can flow into
        the component [kg]
    :type max_input: numerical
    :param trailer_distance: distance for trailer delivery [km]
    :type trailer_distance: numerical
    :param driver_costs: driver costs [EUR/h]
    :type driver_costs: numerical
    :param bus_in: input hydrogen bus [kg]
    :type bus_in: numerical
    :param bus_out: output hydrogen bus [kg]
    :type bus_out: numerical
    :param round_trip_distance: round trip distance from origin to destination [km]
    :type round_trip_distance: numerical
    :param set_parameters(params): updates parameter default values
        (see generic Component class)
    :type set_parameters(params): function
    :param flow_switch: determines whether there is a flow in the current timestep:
        0 = off, 1 = on
    :type flow_switch: int
    """

    def __init__(self, params):
        """Constructor method
        """
        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------ PARAMETERS ------------------
        self.name = 'Gate_default_name'
        self.max_input = None
        self.trailer_distance = 30
        self.driver_costs = 25
        self.bus_in = None
        self.bus_out = None
        self.round_trip_distance = self.trailer_distance * 2

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)

        # ------------------- STATES -------------------
        self.flow_switch = None

    def update_var_costs(self, results, sim_params):
        """Calculates variable costs of the component which only applies if the
        trailer is used, based on the distance travelled by the trailer.

        :param results: oemof results object for this timestep
        :type results: object
        :param sim_params: simulation parameters defined by user
        :type sim_params: object
        """
        # First create an empty cost and art. cost array for this component, if it hasn't been
        # created before.
        if 'variable_costs' not in self.results:
            # If this function is not overwritten in the component, then costs and art. costs are
            # not part of the component and therefore set to 0.
            self.results['variable_costs'] = [0] * sim_params.n_intervals
            self.results['art_costs'] = [0] * sim_params.n_intervals
            # A list is created for the flow switch values
            self.flow_switch = [0] * sim_params.n_intervals

        if self.variable_costs is not None:
            this_dependency_value = self.flows[self.dependency_flow_costs][sim_params.i_interval]
            if this_dependency_value > 0:
                flow_switch_value = 1
            else:
                flow_switch_value = 0
            self.flow_switch[sim_params.i_interval] = flow_switch_value
            self.results['variable_costs'][sim_params.i_interval] = \
                flow_switch_value * self.round_trip_distance * self.variable_costs + \
                flow_switch_value * self.driver_costs

            # Update the artificial costs for this time step [EUR].
            if self.artificial_costs is not None:
                this_dependency_value = \
                    self.flows[self.dependency_flow_costs][sim_params.i_interval]
                self.results['art_costs'][sim_params.i_interval] = \
                    this_dependency_value * self.artificial_costs

    def prepare_simulation(self, components):
        """Updates artificial costs for this time step (dependent on foreign
        states) and determines the maximum hydrogen input for the
        component.

        :param components: List containing each component object
        :type components: list
        :return: artificial costs and maximum allowed hydrogen input
        """
        if self.fs_component_name is not None:
            origin_available_storage_level = self.get_foreign_state_value(components, index=0)
            available_storage_level_used = \
                self.get_foreign_state_value(components, index=1)\
                - self.get_foreign_state_value(components, index=2)
            half_capacity = self.get_foreign_state_value(components, index=3) / 2
            fs_destination_storage_level_kg = self.get_foreign_state_value(components, index=4)
            fs_destination_storage_capacity = self.get_foreign_state_value(components, index=5)
            fs_destination_storage_threshold = self.get_foreign_state_value(components, index=6)
            if origin_available_storage_level == min(available_storage_level_used, half_capacity) \
                    and fs_destination_storage_level_kg < \
                    fs_destination_storage_threshold * fs_destination_storage_capacity:
                self.max_input = 1000e6
            else:
                self.max_input = 0

    def create_oemof_model(self, busses, _):
        """Creates an oemof Transformer component from the information given in the
        TrailerGate class, to be used in the oemof model.

        :param busses: list of the virtual buses used in the energy system
        :type busses: list
        :return: the 'trailer_gate' oemof component
        """
        trailer_gate = solph.Transformer(
            label=self.name,
            inputs={busses[self.bus_in]: solph.Flow(variable_costs=self.artificial_costs,
                                                    nominal_value=self.max_input)},
            outputs={busses[self.bus_out]: solph.Flow()}
        )
        return trailer_gate
