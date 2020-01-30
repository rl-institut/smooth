import oemof.solph as solph
from .component import Component


class CompressorH2(Component):
    def __init__(self, params):
        # Call the init function of th mother class.
        Component.__init__(self)

        """ PARAMERTERS """
        self.name = 'Compressor_default_name'

        # run on MPC
        self.operate_on_mpc = False
        self.mpc_data = 0

        # Busses
        self.bus_h2_in = None
        self.bus_h2_out = None
        self.bus_el = None

        # Max. mass flow [kg/h].
        self.m_flow_max = 33.6

        # Life time [a].
        self.life_time = 20

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

        """ ENERGY NEED FOR COMPRESSION """
        # Specific compression energy (electrical energy needed per kg H2) [Wh/kg].
        self.spec_compression_energy = None

    def create_oemof_model(self, busses, _):

        # when operating on mpc the input hydrogen flow is fixed
        if self.operate_on_mpc:
            flow_h2_in = solph.Flow(
                actual_value=self.mpc_data,
                fixed=True,
                nominal_value=self.m_flow_max*self.sim_params.interval_time/60)
        # otherwise all flows are solved by oemof
        else:
            flow_h2_in = solph.Flow(nominal_value=self.m_flow_max*self.sim_params.interval_time/60)

        compressor = solph.Transformer(
            label=self.name,
            inputs={busses[self.bus_h2_in]: flow_h2_in,
                    busses[self.bus_el]: solph.Flow()},
            outputs={busses[self.bus_h2_out]: solph.Flow()},
            conversion_factors={busses[self.bus_h2_in]: 1, busses[self.bus_el]: self.spec_compression_energy,
                                busses[self.bus_h2_out]: 1})

        return compressor

    def prepare_simulation(self, components):
        # The compressor has two foreign states, the inlet pressure and the outlet pressure. Usually this is the storage
        # pressure of the storage at that bus. But a fixed pressure can also be set.

        # Get the inlet pressure [bar].
        p_in = self.get_foreign_state_value(components, 0)
        # Get the outlet pressure [bar].
        p_out = self.get_foreign_state_value(components, 1)

        # ToDO: Calculate the specific compression energy with help of the input and output pressure.
        # Set the specific compression energy [Wh/kg].
        self.spec_compression_energy = 2000


