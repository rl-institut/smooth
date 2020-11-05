import oemof.solph as solph
from .component import Component


class TrailerH2Delivery(Component):
    """Component created for a hydrogen trailer delivery"""

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

        # Trailer capacity (at maximum pressure) [kg]
        self.trailer_capacity = 900

        # Define the threshold value for the artificial costs.
        # The threshold for the destination storage to encourage/discourage the use of the trailer
        # (percentage of capacity) [-]
        self.fs_destination_storage_threshold = None
        # The amount of hydrogen needed [kg]
        self.hydrogen_needed = 0
        # The amount of hydrogen needed [kg]
        self.fs_origin_available_kg = None

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)

        # ------------------- INTERNAL VALUES -------------------
        # The current artificial cost value [EUR/kg].
        self.current_ac = 0

    def prepare_simulation(self, components):
        # Check level of destination storage component: if it is below specified threshold,
        # implement low artificial costs (to encourage system to fill it)
        # Check level of all non-central storage component and use the one with the
        # highest amount of h2:
        # if it is below specified threshold, the trailer cannot take any hydrogen from it

        # In the model definition, the foreign states must be defined in the following order:
        # 1) all origin storage levels [kg]
        # 2) all origin minimum storage levels [kg]
        # 3) all origin capacities [kg]
        # 4) destination storage level [kg]
        # 5) destination scapacity [kg]
        # The order for each of these in terms of production sites must also be the same e.g.
        # the first entry relates to the first site, the second entry relates
        # to the second site etc.
        if self.fs_component_name is not None:

            # n is the number of production sites that the trailer is connected to
            n = int((len(self.fs_component_name) - 2) / 3)
            # Creates an index list for the number of foreign states considered
            index_list = list(range(0, len(self.fs_component_name)))
            # List containing the origin storage levels [kg]
            fs_origin_storage_levels = []
            # List containing the origin minimum storage levels [kg]
            fs_origin_min_storage_levels = []
            # List containing the origin capacities [kg]
            fs_origin_capacities = []
            # List containing the origin available masses [kg]
            fs_origin_available_masses = []

            # Obtains a list of the origin storage levels for n sites
            for i in index_list[0:n]:
                this_origin_storage_level = self.get_foreign_state_value(components, index=i)
                fs_origin_storage_levels.append(this_origin_storage_level)

            # Obtains a list of the origin minimum storage levels for n sites
            for i in index_list[n:2*n]:
                this_min_storage_level = self.get_foreign_state_value(components, index=i)
                fs_origin_min_storage_levels.append(this_min_storage_level)

            # Obtains a list of the origin capacity levels for n sites
            for i in index_list[2*n:3*n]:
                this_capacity = self.get_foreign_state_value(components, index=i)
                fs_origin_capacities.append(this_capacity)

            # Obtains a list for the available masses that can be taken from the
            # origin storage [kg].
            # It cannot take more than half of the capacity into account
            for i in range(int(n)):
                this_available_kg = min((fs_origin_storage_levels[i]
                                         - fs_origin_min_storage_levels[i]),
                                        fs_origin_capacities[i] / 2)
                fs_origin_available_masses.append(this_available_kg)

            # Get the availability mass of hydrogen of the fullest origin storage
            self.fs_origin_available_kg = max(fs_origin_available_masses)
            # Obtains the destination storage level [kg]
            fs_destination_storage_level = \
                self.get_foreign_state_value(components, index=index_list[-2])
            # Obtains the destination storage capacity [kg]
            fs_destination_capacity = \
                self.get_foreign_state_value(components, index=index_list[-1])
            # Obtains the available mass that can be delivered to the destination storage [kg]
            fs_destination_available_storage = \
                fs_destination_capacity - fs_destination_storage_level

            # Checks if the destination storage level is below the threshold:
            # if yes, delivery possible

            # todo: implement multiple storage delivery in one time step from different wind
            #  parks - low priority

            if fs_destination_storage_level \
                    < self.fs_destination_storage_threshold * fs_destination_capacity:

                # If the available mass [kg] in the destination storage and the amount of
                # available hydrogen [kg] in the origin storage exceed the trailer capacity,
                # the trailer should be completely filled
                if fs_destination_available_storage >= self.trailer_capacity \
                        and self.fs_origin_available_kg >= self.trailer_capacity:
                    self.hydrogen_needed = self.trailer_capacity
                # If the available mass [kg] in the destination storage exceeds the trailer
                # capacity but the amount of available hydrogen in the origin storage is less
                # than the trailer capacity, the trailer should be filled with the maximum amount
                # of available hydrogen from the origin storage
                elif fs_destination_available_storage > \
                        self.trailer_capacity > self.fs_origin_available_kg:
                    self.hydrogen_needed = self.fs_origin_available_kg
                # Else, the trailer should deliver the maximum amount of hydrogen that can fit
                # into the destination storage
                else:
                    self.hydrogen_needed = fs_destination_available_storage
            # If the destination storage level is not below the threshold no delivery possible
            else:
                self.hydrogen_needed = 0

        self.current_ac = self.get_costs_and_art_costs()

    def create_oemof_model(self, busses, _):
        trailer = solph.Transformer(
            label=self.name,
            outputs={busses[self.bus_out]: solph.Flow(variable_costs=self.current_ac)},
            inputs={busses[self.bus_in]: solph.Flow(nominal_value=self.hydrogen_needed)})
        return trailer
