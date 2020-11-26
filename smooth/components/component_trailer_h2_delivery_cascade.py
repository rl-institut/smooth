"""
This module represents a hydrogen trailer delivery from a single
production site to one main destination site, and a secondary
destination site that is dependent on the main site when
necessary.

*****
Scope
*****
Hydrogen trailers can be crucial in an energy system as a means of transporting
hydrogen from the production site to the destination site (e.g. a refuelling
station). Sometimes it is the case that one production site should supply
hydrogen to destination sites that are in close proximity to each other, for
instance. If this is the case, it is beneficial for the energy system
productivity to supply to both storages in one trip. This component represents
a case where there is one main destination site that needs regular delivery,
and one secondary destination site that will receive a delivery in the same
trip as to the main destination site when necessary.

*******
Concept
*******
The cascade hydrogen trailer component is also a transformer component with a
hydrogen bus input and output that are distinct from each other. This component
should be used in parallel with the trailer gate and trailer gate cascade
components. The amount of hydrogen that can be transported in a given time step
is determined, and this value restricts the flow in the component.

.. figure:: /images/trailer_h2_delivery.png
    :width: 60 %
    :alt: trailer_h2_delivery.png
    :align: center
    Fig.1: Simple diagram of a hydrogen delivery trailer

Trailer activity
----------------
In this component, the trailer has the option of transporting hydrogen
from one production site to two destination sites that are dependent
on one another. Thresholds are set for the origin and destination storages.
The component then:

* Checks the level of the origin storage component: if it is below specified
  threshold, the trailer cannot take hydrogen from it.
* Checks the level of destination storage components: if they are both below
  their specified thresholds, then the trailer is incentivised to deliver
  to both storages.
* Checks the mass of hydrogen in all storages as well as the trailer
  capacity, and transports the maximum possible amount of hydrogen.
* Calculates how much hydrogen should get delivered to the main and
  secondary destination storages, prioritising filling up the main
  storage when necessary.
"""


import oemof.solph as solph
from .component import Component
from oemof.outputlib import views


class TrailerH2DeliveryCascade(Component):
    """
    :param name: unique name given to the trailer component
    :type name: str
    :param bus_in: input hydrogen bus to the trailer
    :type bus_in: str
    :param bus_out: output hydrogen bus from the trailer
    :type bus_out: str
    :param trailer_capacity: trailer capacity [kg]
    :type trailer_capacity: numerical
    :param fs_destination_storage_threshold_1: threshold for main destination
        storage to encourage/discourage the use of the trailer [-]
    :type fs_destination_storage_threshold_1: numerical
    :param fs_destination_storage_threshold_2: threshold for secondary destination
        storage to encourage/discourage delivery to it [-]
    :type fs_destination_storage_threshold_2: numerical
    :param hydrogen_needed: mass of hydrogen needed from delivery [kg]
    :type hydrogen_needed: numerical
    :param output_h2_1: amount of hydrogen delivered to main destination [kg]
    :type output h2_1: numerical
    :param output_h2_2: amount of hydrogen delivered to secondary destination [kg]
    :type output h2_2: numerical
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
        self.fs_destination_storage_threshold_1 = None
        self.fs_destination_storage_threshold_2 = None
        self.hydrogen_needed = 0
        self.output_h2_1 = 0
        self.output_h2_2 = 0
        self.fs_origin_available_kg = None

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)

        # ------------------- INTERNAL VALUES -------------------
        self.current_ac = 0

    def prepare_simulation(self, components):
        """Prepares the simulation by determining trailer activity and parameters such
        as how much hydrogen is needed for delivery and how this should be distributed
        between the destination storages.

        :param components: List containing each component object
        :type components: list
        :return: artificial costs, amount of hydrogen needed and the amounts delivered
            to each storage
        """
        # Check level of destination storage component: if it is below specified threshold,
        # implement low artificial costs (to encourage system to fill it)
        # Check level of all non-central storage component and use the one with the highest amount of h2:
        # if it is below specified threshold, the trailer cannot take any hydrogen from it
        if self.fs_component_name is not None:
            # Obtains the origin storage level [kg]
            fs_origin_storage_level_kg = self.get_foreign_state_value(components, index=0)
            # Obtains the origin min storage level [kg]
            fs_origin_min_storage_level = self.get_foreign_state_value(components, index=1)
            # Obtains the origin capacity [kg]
            fs_origin_capacity = self.get_foreign_state_value(components, index=2)

            # Obtains the available mass that can be taken from the origin storage [kg]
            self.fs_origin_available_kg = min((fs_origin_storage_level_kg - fs_origin_min_storage_level),
                                           fs_origin_capacity/2)
            # Obtains the first destination storage level [kg]
            fs_destination_storage_level_kg_1 = self.get_foreign_state_value(components, index=3)
            # Obtains the first destination storage capacity [kg]
            fs_destination_storage_capacity_1 = self.get_foreign_state_value(components, index=4)
            # Obtains the second destination storage level [kg]
            fs_destination_storage_level_kg_2 = self.get_foreign_state_value(components, index=5)
            # Obtains the second destination storage capacity [kg]
            fs_destination_storage_capacity_2 = self.get_foreign_state_value(components, index=6)

            # Obtains the available mass that can be delivered to the first destination storage [kg]
            fs_destination_available_storage_1 = \
                fs_destination_storage_capacity_1 - fs_destination_storage_level_kg_1

            # Obtains the available mass that can be delivered to the second destination storage [kg]
            fs_destination_available_storage_2 = \
                fs_destination_storage_capacity_2 - fs_destination_storage_level_kg_2

            # check threshold of first storage
            if fs_destination_storage_level_kg_1 \
                    < self.fs_destination_storage_threshold_1 * fs_destination_storage_capacity_1:
                # check threshold of second storage
                if fs_destination_storage_level_kg_2 \
                        < self.fs_destination_storage_threshold_2 * fs_destination_storage_capacity_2:
                    available_storage_tot = \
                        fs_destination_available_storage_1 + fs_destination_available_storage_2

                    # calculate the amount of hydrogen which gets delivered
                    if available_storage_tot >= self.trailer_capacity \
                            and self.fs_origin_available_kg >= self.trailer_capacity:
                        self.hydrogen_needed = self.trailer_capacity
                        # calculate the amount of hydrogen which gets delivered to storage one and two
                        if fs_destination_available_storage_1 >= self.trailer_capacity:
                            self.output_h2_1 = self.trailer_capacity
                            self.output_h2_2 = 0
                        else:
                            self.output_h2_1 = fs_destination_available_storage_1
                            self.output_h2_2 = \
                                self.trailer_capacity - fs_destination_available_storage_1

                    elif available_storage_tot \
                            > self.trailer_capacity > self.fs_origin_available_kg:
                        self.hydrogen_needed = self.fs_origin_available_kg
                        # calculate the amount of hydrogen which gets delivered to storage one and two
                        if self.fs_origin_available_kg <= fs_destination_available_storage_1:
                            self.output_h2_1 = self.fs_origin_available_kg
                            self.output_h2_2 = 0
                        else:
                            self.output_h2_1 = fs_destination_available_storage_1
                            self.output_h2_2 = \
                                self.fs_origin_available_kg - fs_destination_available_storage_1

                    else:
                        self.hydrogen_needed = available_storage_tot
                        self.output_h2_1 = fs_destination_available_storage_1
                        self.output_h2_2 = fs_destination_available_storage_2

                else:
                    available_storage = fs_destination_available_storage_1
                    self.output_h2_2 = 0

                    if available_storage >= self.trailer_capacity \
                            and self.fs_origin_available_kg >= self.trailer_capacity:
                        self.hydrogen_needed = self.trailer_capacity
                        self.output_h2_1 = self.trailer_capacity

                    elif available_storage \
                            > self.trailer_capacity > self.fs_origin_available_kg:
                        self.hydrogen_needed = self.fs_origin_available_kg
                        self.output_h2_1 = self.fs_origin_available_kg

                    else:
                        self.hydrogen_needed = available_storage
                        self.output_h2_1 = available_storage

            else:
                self.hydrogen_needed = 0

        self.current_ac = self.get_costs_and_art_costs()

    def create_oemof_model(self, busses, _):
        """Creates an oemof Transformer component from the information given in the
        TrailerH2DeliveryCascade class, to be used in the oemof model.

        :param busses: list of the virtual buses used in the energy system
        :type busses: list
        :return: the 'trailer_cascade' oemof component
        """
        trailer_cascade = solph.Transformer(
            label=self.name,
            outputs={busses[self.bus_out]: solph.Flow(variable_costs=self.current_ac)},
            inputs={busses[self.bus_in]: solph.Flow(nominal_value=self.hydrogen_needed)})
        return trailer_cascade



