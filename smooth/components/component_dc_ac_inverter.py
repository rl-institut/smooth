"""
A simple DC-AC inverter component is created through this module.

******
Scope
******
Similarly to AC-DC converters, DC-AC inverters also regulate and shape
electrical signals into the appropriate forms. These inverters are
used in renewable energy systems, for instance, to convert solar
energy into AC power that can then be directly used by other components
in the system.

*******
Concept
*******
The DC-AC inverter component has a DC electricity input and an AC
electricity output that is governed by an efficiency, where the
default value is chosen to be 99% [1]. A maximum output power is
also defined in the component.

References
----------
[1] Sunny Highpower PEAK3 inverter (see manufacturer PDF)
"""

import oemof.solph as solph
from .component import Component


class DCACInverter(Component):
    """
    :param name: unique name given to the DC-AC inverter component
    :type name: str
    :param bus_el_ac: AC electric bus the converter is connected to
    :type bus_el_ac: str
    :param bus_el_dc: DC electric bus the converter is connected to
    :type bus_el_dc: str
    :param output_power_max: maximum output power [W]
    :type output_power_max: numerical
    :param efficiency: efficiency of the inverter [-]
    :type efficiency: numerical
    """

    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = "DC-AC inverter default name"
        self.bus_el_ac = None
        self.bus_el_dc = None
        self.output_power_max = 150000
        self.efficiency = 0.99

    def create_oemof_model(self, busses, _):
        """Creates a simple oemof Transformer component using the information
        given in the DCACInverter class, to be used in the oemof model

        :param busses: virtual buses used in the energy system
        :type busses: list
        :return: 'dc_ac_inverter' oemof component
        """
        dc_ac_inverter = solph.Transformer(
            label=self.name,
            inputs={busses[self.bus_el_dc]: solph.Flow(
                variable_costs=0)},
            outputs={busses[self.bus_el_ac]: solph.Flow(
                nominal_value=self.output_power_max
            )},
            conversion_factors={busses[self.bus_el_ac]: self.efficiency})
        return dc_ac_inverter
