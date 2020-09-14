"""
This module represents a hydrogen trailer delivery.

*****
Scope
*****
Hydrogen trailers can be crucial in an energy system as a means of transporting
hydrogen from the production site to the destination site (e.g. a refuelling
station).

*******
Concept
*******
The hydrogen trailer component is a transformer component with a hydrogen
bus input and a hydrogen bus output, which should be distinct from each other
in order to maintain a one way flow from the production site to the destination
site. The amount of hydrogen that can be transported in a given time step
is determined, and this value restricts the flow in the component.

Trailer activity
----------------
Thresholds are set for both the origin and destination storages. The component
then:

* Checks the level of destination storage component: if it is below specified
  threshold, low artificial costs are implemented (to encourage system to fill it).
* Checks the level of non-central storage component: if it is below specified
  threshold, the trailer cannot take any hydrogen from it.
* Checks the mass of hydrogen in both storages along with taking the trailer
  capacity into consideration, and transports the maximum possible amount of
  hydrogen.
* Considers the round trip distance along with the assumptions that the
  trailer can travel at 100 km/h and that the refuelling time for the trailer
  is 15 minutes. With this information, it is determined whether or not
  delivery is possible for the following time step with the trailer.
"""

import oemof.solph as solph
from .component import Component
from oemof.outputlib import views


class TrailerH2Delivery(Component):
    """
    :param name: unique name given to the h2 trailer delivery component
    :type name: str
    :param bus_in: hydrogen bus that enters the component
    :type bus_in: str
    :param bus_out: hydrogen bus that leaves the component
    :type bus_out: str
    :param trailer_capacity: trailer capacity (at maximum pressure) [kg]
    :type trailer_capacity: numerical
    :param fs_destination_storage_threshold: threshold for the destination storage to
        encourage/discourage the use of the trailer (percentage of capacity) [-]
    :type fs_destination_storage_threshold: numerical
    :param fs_origin_storage_threshold: threshold for the origin storage to
        encourage/discourage the use of the trailer (percentage of capacity) [-]
    :type fs_origin_storage_threshold: numerical
    :param hydrogen_transported: amount of hydrogen transported by the trailer [kg]
    :type hydrogen_transported: numerical
    :param hydrogen_needed: amount of hydrogen needed [kg]
    :type hydrogen_needed: numerical
    :param fs_low_art_cost: low artificial cost value (set for destination storage) [EUR/kg]
    :type fs_low_art_cost: numerical
    :param fs_high_art_cost: high artificial cost value (set for destination storage) [EUR/kg]
    :type fs_high_art_cost: numerical
    :param set_parameters(params): updates parameter default values
        (see generic Component class)
    :type set_parameters(params): function
    :param round_trip_distance: round-trip distance [km]
    :type round_trip_distance: numerical
    :param flow_switch: this determines whether there is a flow in the current
        timestep: 0 = off, 1 = on
    :type flow_switch: int
    :param max_delivery_value: maximum amount of hydrogen that can be delivered in
        the given timestep [kg]
    :type max_delivery_value: numerical
    :param delivery_possible: this states whether or not delivery is possible in the given
        timestep: 0 = no, 1 = yes
    :type delivery_possible: int
    :param current_ac: current artificial cost value [EUR/kg]
    :type current_ac: numerical
    """

    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = 'Trailer_default_name'
        self.bus_in = None
        self.bus_out = None

        # ToDo: Calculate pressure of hydrogen in trailer
        # ToDo: At the moment only the variable costs per distance travelled are taken into
        #  consideration, but the update_var_costs() function can be modified to allow for
        #  the variable costs per kg of hydrogen transported as well
        # ToDo: At the moment, it is assumed that the hydrogen can be delivered within one
        #  hour - this needs to be changed if the single trip distance from the origin to
        #  destination is longer than 45 minutes (1 hour - 15 mins refuelling)

        self.trailer_capacity = 500
        self.single_trip_distance = 30
        # Define the threshold value for the artificial costs.
        self.fs_destination_storage_threshold = None
        self.fs_origin_storage_threshold = None
        self.hydrogen_transported = 0
        self.hydrogen_needed = 0
        self.fs_low_art_cost = None
        self.fs_high_art_cost = None

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)

        self.round_trip_distance = self.single_trip_distance * 2

        # ------------------- STATES -------------------
        self.flow_switch = None
        # This defines the maximum amount of hydrogen that can be delivered in the given timestep:
        # - 0 if the origin storage level is below the specified threshold
        # - else, the capacity of the trailer
        self.max_delivery_value = None
        self.delivery_possible = 1

        # ------------------- INTERNAL VALUES -------------------
        self.current_ac = 0

    def update_var_costs(self, results, sim_params):
        """Tracks the costs and artificial costs of a component for each time step.

        :param results: oemof results for the given time step
        :type results: object
        :param sim_params: simulation parameters for the energy system (defined by user)
        :type sim_params: object
        :return: updated artificial costs for this time step [EUR]
        """
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
                flow_switch_value * self.round_trip_distance * self.variable_costs

            # Update the artificial costs for this time step [EUR].
            if self.artificial_costs is not None:
                this_dependency_value = \
                    self.flows[self.dependency_flow_costs][sim_params.i_interval]
                self.results['art_costs'][sim_params.i_interval] = \
                    this_dependency_value * self.artificial_costs

    def prepare_simulation(self, components):
        """Prepares the simulation by determining whether hydrogen should be transported
        from the origin storage, and if so, how much hydrogen can be transported.

        :param components: List containing each component object
        :type components: list
        """
        # Check level of destination storage component: if it is below specified threshold,
        # implement low artificial costs (to encourage system to fill it)
        # Check level of non-central storage component: if it is below specified threshold, the
        # trailer cannot take any hydrogen from it
        if self.fs_component_name is not None:
            # Obtains the origin storage level [kg]
            fs_origin_storage_level_kg = self.get_foreign_state_value(components, index=0)
            # Obtains the origin storage capacity [kg]
            fs_origin_storage_capacity = self.get_foreign_state_value(components, index=1)
            # Obtains the available mass that can be taken from the origin storage [kg]
            fs_origin_available_kg = \
                fs_origin_storage_level_kg - \
                (self.fs_origin_storage_threshold * fs_origin_storage_capacity)
            # Obtains the destination storage level [kg]
            fs_destination_storage_level_kg = self.get_foreign_state_value(components, index=2)
            # Obtains the destination storage capacity [kg]
            fs_destination_storage_capacity = self.get_foreign_state_value(components, index=3)
            # Obtains the available mass that can be delivered to the destination storage [kg]
            fs_destination_available_storage = \
                fs_origin_storage_capacity - fs_destination_storage_level_kg

            # Checks if the destination storage level is below the threshold: if yes, low
            # artificial costs are implemented to encourage a delivery from the trailer
            if fs_destination_storage_level_kg \
                    < self.fs_destination_storage_threshold * fs_destination_storage_capacity:
                self.artificial_costs = self.fs_low_art_cost
                # If the available mass [kg] in the destination storage and the amount of
                # available hydrogen [kg] in the origin storage exceed the trailer capacity,
                # the trailer should be completely filled
                if fs_destination_available_storage > self.trailer_capacity \
                        and fs_origin_available_kg >= self.trailer_capacity:
                    self.hydrogen_needed = self.trailer_capacity
                # If the available mass [kg] in the destination storage exceeds the trailer
                # capacity but the amount of available hydrogen in the origin storage is less
                # than the trailer capacity, the trailer should be filled with the maximum amount
                # of available hydrogen from the origin storage
                elif fs_destination_available_storage > \
                        self.trailer_capacity > fs_origin_available_kg:
                    self.hydrogen_needed = fs_origin_available_kg
                # Else, the trailer should deliver the maximum amount of hydrogen that can fit
                # into the destination storage
                else:
                    self.hydrogen_needed = fs_destination_available_storage
            # If the destination storage level is not below the threshold, high artificial costs are
            # implemented to discourage unnecessary deliveries
            else:
                self.artificial_costs = self.fs_high_art_cost
            # If the origin storage level is below the specified threshold or the distance is far
            # enough that the trailer cannot complete the round trip plus refuelling in one hour,
            # delivery is not possible from this storage
            if fs_origin_storage_level_kg < \
                    self.fs_origin_storage_threshold * fs_origin_storage_capacity \
                    or self.delivery_possible == 0:
                self.hydrogen_transported = 0
            else:
                self.hydrogen_transported = self.hydrogen_needed

        self.current_ac = self.get_costs_and_art_costs()

    def create_oemof_model(self, busses, _):
        """Creates an oemof Transformer component from the information given in the
        TrailerH2Delivery class, to be used in the oemof model.

        :param busses: List of the virtual buses used in the energy system
        :type busses: list
        :return: 'trailer' oemof component
        """
        trailer = solph.Transformer(
            label=self.name,
            outputs={busses[self.bus_out]: solph.Flow(variable_costs=self.current_ac)},
            inputs={busses[self.bus_in]: solph.Flow(nominal_value=self.hydrogen_transported
                                                    )})
        return trailer

    def update_states(self, results, sim_params):
        """Updates the states of the storage component for each time step.

        :param results: oemof results for the given time step
        :type results: object
        :param sim_params: simulation parameters for the energy system (defined by user)
        :type sim_params: object
        :return: updated state values for each state in the 'state' dict
        """
        data_trailer = views.node(results, self.name)
        df_trailer = data_trailer['sequences']

        for i_result in df_trailer:
            if 'is_delivery_possible' not in self.states:
                self.states['is_delivery_possible'] = [None] * sim_params.n_intervals

            if i_result[0][1] == self.name and i_result[1] == 'flow':
                # The amount of hydrogen entering the trailer is recorded
                this_h2_delivered = df_trailer[i_result][0]
                # If the trailer is used (this_h2_delivered > 0) and under the assumption that:
                # - it takes 15 minutes for the trailer to refuel
                # - the trailer can travel at 100 km/h so 75 km in 45 minutes
                if this_h2_delivered > 0 and self.round_trip_distance > 75:
                    # if the trailer is located too far away, delivery is not possible
                    # for the next timestep
                    self.delivery_possible = 0
                else:
                    self.delivery_possible = 1

                self.states['is_delivery_possible'][sim_params.i_interval] = self.delivery_possible
