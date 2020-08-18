import oemof.solph as solph
from .component import Component
from oemof.outputlib import views


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
        # The amount of hydrogen transported by the trailer [kg]
        self.hydrogen_transported = 0
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
        # Check level of all non-central storage component and use the one with the highest amount of h2:
        # if it is below specified threshold, the trailer cannot take any hydrogen from it
        if self.fs_component_name is not None:
            # Obtains the origin storage level [kg]
            fs_origin_storage_level_kg_1 = self.get_foreign_state_value(components, index=0)
            # Obtains the origin min storage level [kg]
            fs_origin_min_storage_level_1 = self.get_foreign_state_value(components, index=1)

            # Obtains the origin storage level [kg]
            fs_origin_storage_level_kg_2 = self.get_foreign_state_value(components, index=2)
            # Obtains the origin min storage level [kg]
            fs_origin_min_storage_level_2 = self.get_foreign_state_value(components, index=3)

            # Obtains the origin storage level [kg]
            fs_origin_storage_level_kg_3 = self.get_foreign_state_value(components, index=4)
            # Obtains the origin storage capacity [kg]
            fs_origin_min_storage_level_3 = self.get_foreign_state_value(components, index=5)

            # Obtains the origin storage level [kg]
            fs_origin_storage_level_kg_4 = self.get_foreign_state_value(components, index=6)
            # Obtains the origin min storage level [kg]
            fs_origin_min_storage_level_4 = self.get_foreign_state_value(components, index=7)

            # Obtains the available mass that can be taken from the origin storage [kg]
            fs_origin_available_kg_1 = fs_origin_storage_level_kg_1 - fs_origin_min_storage_level_1
            fs_origin_available_kg_2 = fs_origin_storage_level_kg_2 - fs_origin_min_storage_level_2
            fs_origin_available_kg_3 = fs_origin_storage_level_kg_3 - fs_origin_min_storage_level_3
            fs_origin_available_kg_4 = fs_origin_storage_level_kg_4 - fs_origin_min_storage_level_4

            # Get the availability mass of hydrogen of the fullest origin storage
            self.fs_origin_available_kg = min(fs_origin_available_kg_1, fs_origin_available_kg_2,
                                              fs_origin_available_kg_3, fs_origin_available_kg_4)

            # Obtains the destination storage level [kg]
            fs_destination_storage_level_kg = self.get_foreign_state_value(components, index=8)
            # Obtains the destination storage capacity [kg]
            fs_destination_storage_capacity = self.get_foreign_state_value(components, index=9)

            # Obtains the available mass that can be delivered to the destination storage [kg]
            fs_destination_available_storage = \
                fs_destination_storage_capacity - fs_destination_storage_level_kg

            # Checks if the destination storage level is below the threshold:
            # if yes, delivery possible
            # todo: implement multiple storage delivery in one time step from different wind parks - low prio

            if fs_destination_storage_level_kg \
                    < self.fs_destination_storage_threshold * fs_destination_storage_capacity:

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
