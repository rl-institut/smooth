"""
A cascade trailer gate component is created to control the output flows from
a trailer delivery to a destination site.

*****
Scope
*****
Similarly to the other gate components, the cascade trailer gate component is
virtual and would not be found in a real life energy system. This component
is used in parallel with the trailer cascade component to control how
hydrogen is distributed between destination sites in the same trip.

*******
Concept
*******
A transformer component is used with a hydrogen bus input and a hydrogen bus
output, where the hydrogen is inputted from the trailer and outputted to the
destination site. The amount of hydrogen that can be delivered to the
destination site is restricted by the maximum input value that is determined
in the cascade trailer component. Notably, a different gate component
should be created for each destination site.
"""


import oemof.solph as solph
from .component import Component


class TrailerGateCascade(Component):
    """
    :param name: unique name given to the cascade trailer gate component
    :type name: str
    :param max_input: maximum mass of hydrogen that can flow into the
        component [kg]
    :type max_input: numerical
    :param bus_in: input hydrogen bus [kg]
    :type bus_in: numerical
    :param bus_out: output hydrogen bus [kg]
    :type bus_out: numerical
    :param set_parameters(params): updates parameter default values
        (see generic Component class)
    :type set_parameters(params): function
    """

    def __init__(self, params):
        """Constructor method
        """
        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------- PARAMETERS -----------------
        self.name = 'Gate_default_name'
        self.max_input = None
        self.bus_in = None
        self.bus_out = None

        # ------------- UPDATE PARAMETER DEFAULT VALUES -------------
        self.set_parameters(params)

    def prepare_simulation(self, components):
        """Sets the maximum input of the component by using the value
        calculated in the cascade trailer component as a foreign state.

        :param components: List containing each component object
        :type components: list
        :return: maximum allowed hydrogen input
        """
        if self.fs_component_name is not None:
            self.max_input = self.get_foreign_state_value(components, index=0)

    def create_oemof_model(self, busses, _):
        """Creates an oemof Transformer component from the information given in the
        TrailerGateCascade class, to be used in the oemof model.

        :param busses: list of the virtual buses used in the energy system
        :type busses: list
        :return: the 'trailer_gate_cascade' oemof component
        """
        trailer_gate_cascade = solph.Transformer(
            label=self.name,
            inputs={busses[self.bus_in]: solph.Flow(nominal_value=self.max_input)},
            outputs={busses[self.bus_out]: solph.Flow()}
        )
        return trailer_gate_cascade
