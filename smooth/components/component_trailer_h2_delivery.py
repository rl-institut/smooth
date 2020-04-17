import oemof.solph as solph
from .component import Component
from oemof.outputlib import views


class TrailerH2Delivery(Component):
    """Component created for a hydrogen trailer delivery"""

    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)

        """ PARAMETERS """
        self.name = 'Trailer_default_name'

        self.bus_in = None
        self.bus_out = None

        # ToDo: Calculate pressure of hydrogen in trailer
        # ToDo: At the moment only the variable costs per distance travelled are taken into consideration,
        #  but the update_var_costs() function can be modified to allow for the variable costs per kg of
        #  hydrogen transported as well
        # At the moment, it is assumed that the hydrogen can be delivered within one hour - this needs to be
        # changed

        # Trailer capacity (at maximum pressure) [kg]
        self.trailer_capacity = 500

        # Single trip distance [km]
        self.single_trip_distance = 30

        # Define the threshold value for the artificial costs.
        # The threshold for the destination storage to encourage/discourage the use of the trailer
        self.fs_destination_storage_threshold = None
        # The threshold for the origin storage to encourage/discourage the use of the trailer
        self.fs_origin_storage_threshold = None
        # The amount of hydrogen transported by the trailer
        self.hydrogen_transported = 0
        # The amount of hydrogen needed
        self.hydrogen_needed = 0
        # Define the low and the high art. cost value (these will be set for the destination storage) [EUR/kg]
        self.fs_low_art_cost = None
        self.fs_high_art_cost = None

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

        # Round-trip distance [km]
        self.round_trip_distance = self.single_trip_distance * 2

        """ STATES """
        # This determines whether there is a flow in the current timestep: 0 = off, 1 = on
        self.flow_switch = None
        # This defines the maximum amount of hydrogen that can be delivered in the given timestep:
        # - 0 if the origin storage level is below the specified threshold
        # - else, the capacity of the trailer
        self.max_delivery_value = None
        # This states whether or not delivery is possible in the given timestep: 0 = no, 1 = yes
        self.delivery_possible = 1

        """ INTERNAL VALUES """
        # The current artificial cost value [EUR/kg].
        self.current_ac = 0

    def update_var_costs(self, results, sim_params):
        # Track the costs and artificial costs of a component for each time step.
        # Parameters:
        #  results: oemof result object for this time step.
        #  sim_params: simulation parameters defined by the user.
        # In this component, the variable costs are calculated differently to the other components, to
        # only apply if the trailer is used based on the distance travelled by the trailer.

        # First create an empty cost and art. cost array for this component, if it hasn't been created before.
        if 'variable_costs' not in self.results:
            # If this function is not overwritten in the component, then costs and art. costs are not part of the
            # component and therefore set to 0.
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
            self.results['variable_costs'][sim_params.i_interval] = flow_switch_value * self.round_trip_distance * self.variable_costs

            # Update the artificial costs for this time step [EUR].
            if self.artificial_costs is not None:
                this_dependency_value = self.flows[self.dependency_flow_costs][sim_params.i_interval]
                self.results['art_costs'][sim_params.i_interval] = this_dependency_value * self.artificial_costs


    def prepare_simulation(self, components):
        # Check level of destination storage component: if it is below specified threshold, implement
        # low artificial costs (to incentivize system to fill it)
        # Check level of non-central storage component: if it is below specified threshold, the
        # trailer cannot take any hydrogen from it
        if self.fs_component_name is not None:
            # Obtains the origin storage pressure level
            fs_origin_storage_level_pressure = self.get_foreign_state_value(components, index=0)
            # Obtains the destination storage pressure level
            fs_destination_storage_level_pressure = self.get_foreign_state_value(components, index=1)
            # Obtains the destination storage capacity [kg]
            fs_destination_storage_capacity = self.get_foreign_state_value(components, index=2)
            # Obtains the destination storage level [kg]
            fs_destination_storage_level_kg = self.get_foreign_state_value(components, index=3)
            if fs_destination_storage_level_pressure < self.fs_destination_storage_threshold:
                self.artificial_costs = self.fs_low_art_cost
                if fs_destination_storage_capacity > self.trailer_capacity:
                    self.hydrogen_needed = self.trailer_capacity
                    self.artificial_costs = self.fs_low_art_cost
                else:
                    self.hydrogen_needed = fs_destination_storage_capacity - fs_destination_storage_level_kg
            else:
                self.artificial_costs = self.fs_high_art_cost
            if fs_origin_storage_level_pressure < self.fs_origin_storage_threshold or self.delivery_possible == 0:
                self.hydrogen_transported = 0
            else:
                self.hydrogen_transported = self.hydrogen_needed



        self.current_ac = self.get_costs_and_art_costs()


    def create_oemof_model(self, busses, _):
        trailer = solph.Transformer(
            label=self.name,
            outputs={busses[self.bus_out]: solph.Flow(variable_costs=self.current_ac)},
            inputs={busses[self.bus_in]: solph.Flow(nominal_value=self.hydrogen_transported
                                                    )})
        return trailer

    def update_states(self, results, sim_params):
        data_trailer = views.node(results, self.name)
        df_trailer = data_trailer['sequences']

        for i_result in df_trailer:
            if 'is_delivery_not_possible' not in self.states:
                self.states['is_delivery_not_possible'] = [None] * sim_params.n_intervals

            if i_result[0][1] == self.name and i_result[1] == 'flow':
                # The amount of hydrogen entering the trailer is recorded
                this_h2_delivered = df_trailer[i_result][0]
                # If the trailer is used (this_h2_delivered > 0) and under the assumption that:
                # - it takes 15 minutes for the trailer to refuel
                # - the trailer can travel at 100 km/h so 75 km in 45 minutes
                if this_h2_delivered > 0 and self.round_trip_distance > 75:
                    # if the trailer is located too far away, delivery is not possible for the next timestep
                    self.delivery_possible = 0
                else:
                    self.delivery_possible = 1

                self.states['is_delivery_not_possible'][sim_params.i_interval] = self.delivery_possible






