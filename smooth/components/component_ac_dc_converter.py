"""
This module represents an AC-DC converter.

******
Scope
******
AC-DC converters play an important role in diverse renewable energy
systems, by regulating and shaping electrical signals in the
appropriate forms for other components in the system and the demands.

*******
Concept
*******
A simple AC-DC converter component is created which intakes an AC electric
bus and transforms it into a DC electric bus with an assumed constant
efficiency. The default efficiency is taken to be 95%, as stated in [1][2],
but this value can be modified by the user in the model definition. The
amount of electricity that can leave the converter is limited by the defined
maximum power.

.. figure:: /images/ac_dc_converter.png
    :width: 60 %
    :alt: ac_dc_converter.png
    :align: center

    Fig.1: Simple diagram of an AC-DC converter.

References
----------
[1] Harrison, K.W. et. al. (2009). The Wind-to-Hydrogen Project: Operational Experience,
Performance Testing, and Systems Integration, NREL.
https://www.nrel.gov/docs/fy09osti/44082.pdf
[2] Hayashi, Y. (2013). High Power Density Rectifier for Highly Efficient Future DC
Distribution System, NTT Facilities Japan.
"""

import oemof.solph as solph
from .component import Component


class ACDCConverter(Component):
    """
    :param name: unique name given to the AC-DC converter component
    :type name: str
    :param bus_el_ac: AC electric bus the converter is connected to
    :type bus_el_ac: str
    :param bus_el_dc: DC electric bus the converter is connected to
    :type bus_el_dc: str
    :param output_power_max: maximum output power [W]
    :type output_power_max: numerical
    :param efficiency: efficiency of the converter
    :type efficiency: numerical

    """

    def __init__(self, params):
        """Constructor method
        """
        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = "AC-DC converter default name"
        # Define the AC electric bus the converter is connected to
        self.bus_el_ac = None
        # Define the DC electric bus the converter is connected to
        self.bus_el_dc = None

        # Max. output power [W]
        self.output_power_max = 10000

        # The efficiency of an AC-DC converter
        self.efficiency = 0.95

    def create_oemof_model(self, busses, _):
        """Creates an oemof Transformer component using the information given in
        the ACDCConverter class, to be used in the oemof model

        :param busses: virtual buses used in the energy system
        :type busses: list
        :return: the oemof AC DC converter component
        """
        ac_dc_converter = solph.Transformer(
            label=self.name,
            inputs={busses[self.bus_el_ac]: solph.Flow(
                variable_costs=0)},
            outputs={busses[self.bus_el_dc]: solph.Flow(
                nominal_value=self.output_power_max
            )},
            conversion_factors={busses[self.bus_el_dc]: self.efficiency})
        return ac_dc_converter
