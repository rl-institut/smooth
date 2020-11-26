"""
This module represents a hydrogen trailer delivery from a single
production site.

*****
Scope
*****
Hydrogen trailers can be crucial in an energy system as a means of transporting
hydrogen from the production site to the destination site (e.g. a refuelling
station).

*******
Concept
*******
Similarly to the hydrogen trailer component with multiple production sites, the
single hydrogen trailer component is a transformer component with a hydrogen
bus input and a hydrogen bus output, which should be distinct from each other in
order to maintain a one way flow from the production site to the destination site.
The only difference between this component and the hydrogen trailer component is
that here, there is only one option for the origin storage and this is
predetermined. This component should be used in parallel with the trailer gate
component. The amount of hydrogen that can be transported in a given time step
is determined, and this value restricts the flow in the component.

.. figure:: /images/trailer_h2_delivery.png
    :width: 60 %
    :alt: trailer_h2_delivery.png
    :align: center
    Fig.1: Simple diagram of a hydrogen delivery trailer

Trailer activity
----------------
Thresholds are set for both the origin and destination storages. The component
then:
* Checks the level of destination storage component: if it is below specified
  threshold, low artificial costs are implemented (to encourage system to fill it).
* Checks the level of origin storage component: if it is below specified
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


class TrailerH2DeliverySingle(Component):
    """
    :param name: unqiue name given to the trailer component
    :type name: str
    :param bus_in: input hydrogen bus to the trailer
    :type bus_in: str
    :param bus_out: output hydrogen bus from the trailer
    :type bus_out: str
    :param trailer_capacity: trailer capacity [kg]
    :type trailer_capacity: numerical
    :param fs_destination_storage_threshold: threshold for destination storage
        to encourage/discourage the use of the trailer [-]
    :type fs_destination_storage_threshold: numerical
    :param hydrogen_needed: mass of hydrogen needed from delivery [kg]
    :type hydrogen_needed: numerical
    :param fs_origin_available_kg: foreign state for the available mass of hydrogen
        in the origin storage [kg]
    :type fs_origin_available_kg: numerical
    :param set_parameters(params): updates parameter default values
        (see generic Component class)
    :type set_parameters(params): function
    :param current_ac: current artificial cost value [EUR/kg]
    :type current_ac: numerical
    """

    def __init__(self, params):
        """Constructor method
        """
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

        self.trailer_capacity = 900
        self.fs_destination_storage_threshold = None
        self.hydrogen_needed = 0
        self.fs_origin_available_kg = None

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)

        # ------------------- INTERNAL VALUES -------------------
        self.current_ac = 0

    def prepare_simulation(self, components):
        """Prepares the simulation by determining trailer activity and how much
        hydrogen is needed

        :param components: List containing each component object
        :type components: list
        :return: artificial costs and the amount of hydrogen needed
        """
        # Check level of destination storage component: if it is below specified threshold,
        # implement low artificial costs (to encourage system to fill it)
        # Check level of all non-central storage component and use the one with the
        # highest amount of h2:
        # if it is below specified threshold, the trailer cannot take any hydrogen from it
        if self.fs_component_name is not None:
            # Obtains the origin storage level [kg]
            fs_origin_storage_level_kg_1 = self.get_foreign_state_value(components, index=0)
            # Obtains the origin min storage level [kg]
            fs_origin_min_storage_level_1 = self.get_foreign_state_value(components, index=1)
            # Obtains the origin capacity [kg]
            fs_origin_capacity_1 = self.get_foreign_state_value(components, index=2)

            # Obtains the available mass that can be taken from the origin storage [kg]
            fs_origin_available_kg_1 = min((fs_origin_storage_level_kg_1 -
                                            fs_origin_min_storage_level_1),
                                           fs_origin_capacity_1/2)

            # Get the availability mass of hydrogen of the fullest origin storage
            self.fs_origin_available_kg = fs_origin_available_kg_1

            # Obtains the destination storage level [kg]
            fs_destination_storage_level_kg = self.get_foreign_state_value(components, index=3)
            # Obtains the destination storage capacity [kg]
            fs_destination_storage_capacity = self.get_foreign_state_value(components, index=4)

            # Obtains the available mass that can be delivered to the destination storage [kg]
            fs_destination_available_storage = \
                fs_destination_storage_capacity - fs_destination_storage_level_kg

            # Checks if the destination storage level is below the threshold:
            # if yes, delivery possible
            # todo: implement multiple storage delivery in one time step from
            #  different wind parks - low prio

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
        """Creates an oemof Transformer component from the information given in the
        TrailerH2DeliverySingle class, to be used in the oemof model.

        :param busses: list of the virtual buses used in the energy system
        :type busses: list
        :return: the 'trailer_single' oemof component
        """
        trailer_single = solph.Transformer(
            label=self.name,
            outputs={busses[self.bus_out]: solph.Flow(variable_costs=self.current_ac)},
            inputs={busses[self.bus_in]: solph.Flow(nominal_value=self.hydrogen_needed)})
        return trailer_single
