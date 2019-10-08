import oemof.solph as solph
from .component import Component


class CompressorH2(Component):
    def __init__(self, params):
        # Call the init function of th mother class.
        Component.__init__(self)

        """ PARAMERTERS """
        self.name = 'Compressor_default_name'

        # Busses
        self.bus_h2_in = None
        self.bus_h2_out = None
        self.bus_el = None

        # Max. mass flow [kg/h].
        self.m_flow_max = 33.6
        # Max. pressure [bar].
        self.p_max = 1000
        # Life time [a].
        self.life_time = 20

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

    def create_oemof_model(self, busses, sim_params):
        compressor = solph.Transformer(
            label=self.name,
            inputs={busses[self.bus_h2_in]: solph.Flow()},
            outputs={busses[self.bus_h2_out]: solph.Flow(), busses[self.bus_el]: solph.Flow()},
            conversion_factors={busses[self.bus_h2_out]: 1, busses[self.bus_el]: -1000})

        return compressor
