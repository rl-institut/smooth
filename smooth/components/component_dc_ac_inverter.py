import oemof.solph as solph
from .component import Component


class DCACInverter(Component):
    """ DC-AC inverter is created through this class """

    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = "DC-AC inverter default name"
        # Define the AC electric bus the converter is connected to
        self.bus_el_ac = None
        # Define the DC electric bus the converter is connected to
        self.bus_el_dc = None

        # Max. output power [W]
        self.output_power_max = 150000
        # Efficiency based on Sunny Highpower PEAK3 inverter (see manufacturer PDF)
        self.efficiency = 0.99

    def create_oemof_model(self, busses, _):
        dc_ac_inverter = solph.Transformer(
            label=self.name,
            inputs={busses[self.bus_el_dc]: solph.Flow(
                variable_costs=0)},
            outputs={busses[self.bus_el_ac]: solph.Flow(
                nominal_value=self.output_power_max
            )},
            conversion_factors={busses[self.bus_el_ac]: self.efficiency})
        return dc_ac_inverter
