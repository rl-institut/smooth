import oemof.solph as solph
from .component import Component


class ACDCConverter(Component):
    """ AC-DC power converter is created through this class """

    def __init__(self, params):

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

        # The efficiency of an AC-DC converter, stated in:
        # Harrison, K.W. et. al. (2009). The Wind-to-Hydrogen Project: Operational Experience,
        # Performance Testing, and Systems Integration, NREL.
        # https://www.nrel.gov/docs/fy09osti/44082.pdf
        # Hayashi, Y. (2013). High Power Density Rectifier for Highly Efficient Future DC
        # Distribution System, NTT Facilities Japan.
        self.efficiency = 0.95

    def create_oemof_model(self, busses, _):
        ac_dc_converter = solph.Transformer(
            label=self.name,
            inputs={busses[self.bus_el_ac]: solph.Flow(
                variable_costs=0)},
            outputs={busses[self.bus_el_dc]: solph.Flow(
                nominal_value=self.output_power_max
            )},
            conversion_factors={busses[self.bus_el_dc]: self.efficiency})
        return ac_dc_converter
