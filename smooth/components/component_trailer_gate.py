import oemof.solph as solph
from .component import Component


class TrailerGate(Component):
    """Gate component is created to transform individual specific buses into one general bus"""

    def __init__(self, params):
        # Call the init function of the mother class.
        Component.__init__(self)

        """ PARAMERTERS """
        self.name = 'Gate_default_name'

        self.max_input = None
        # distance for trailer delivery
        self.trailer_distance = 30
        # Driver costs [€/h]
        self.driver_costs = 25

        # Busses
        self.bus_in = None
        self.bus_out = None

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

        # ------------------- STATES -------------------
        # This determines whether there is a flow in the current timestep: 0 = off, 1 = on
        self.flow_switch = None

        self.round_trip_distance = self.trailer_distance * 2

    def update_var_costs(self, results, sim_params):
        # Track the costs and artificial costs of a component for each time step.
        # Parameters:
        #  results: oemof result object for this time step.
        #  sim_params: simulation parameters defined by the user.
        # In this component, the variable costs are calculated differently to the other components,
        # to only apply if the trailer is used based on the distance travelled by the trailer.

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
        # Update the artificial costs for this time step (dependant on foreign states).
        if self.fs_component_name is not None:
            origin_available_storage_level = self.get_foreign_state_value(components, index=0)
            available_storage_level_used = self.get_foreign_state_value(components, index=1) - \
                                           self.get_foreign_state_value(components, index=2)
            if origin_available_storage_level == available_storage_level_used:
                self.max_input = 0

    def create_oemof_model(self, busses, _):
        trailer_gate = solph.Transformer(
            label=self.name,
            inputs={busses[self.bus_in]: solph.Flow(variable_costs=self.artificial_costs,
                                                    nominal_value=self.max_input)},
            outputs={busses[self.bus_out]: solph.Flow()}
        )
        return trailer_gate
