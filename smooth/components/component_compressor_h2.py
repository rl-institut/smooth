import oemof.solph as solph
from .component import Component
from .component_functions.all_component_functions import calculate_compressibility_factor
from math import log


class CompressorH2(Component):
    """Compressor agents for compressing hydrogen are created through this class

    :param name: unique name of the component
    :type name: str
    :param bus_h2_in: name of the lower pressure hydrogen bus
    :type bus_h2_in: str
    :param bus_h2_out: name of the higher pressure hydrogen bus
    :type bus_h2_out: str
    :param bus_el: name of the electric bus that provides energy to run the compressor
    :type bus_el: str
    :param m_flow_max: maximum mass flow through the compressor in kg/h
    :type m_flow_max: float
    """

    def __init__(self, params):
        # Call the init function of th mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
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

        # It is assumed that hydrogen always enters the compressor at room temperature [K]
        # FIXME: An assumption from MATLAB is that hydrogen always enters the
        # compressor at this temp, should it be calculated instead of assumed??

        self.temp_in = 293.15

        # Overall efficiency of the compressor (value taken from MATLAB) [-]
        self.efficiency = 0.88829

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)

        # ------------------- ENERGY NEED FOR COMPRESSION -------------------
        # Specific compression energy (electrical energy needed per kg H2) [Wh/kg].
        self.spec_compression_energy = None

        # ------------------- CONSTANT PARAMETERS -------------------
        # Mr_H2 = Molar mass of H2 [kg/mol], R = the gas constant (R) [J/(K*mol)]
        self.R = 8.314
        self.Mr_H2 = 2.016 * 1e-3
        self.R_H2 = self.R / self.Mr_H2

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
            conversion_factors={
                busses[self.bus_h2_in]: 1,
                busses[self.bus_el]: self.spec_compression_energy,
                busses[self.bus_h2_out]: 1})

        return compressor

    def prepare_simulation(self, components):
        # The compressor has two foreign states, the inlet pressure and the
        # outlet pressure. Usually this is the storage pressure of the storage
        # at that bus. But a fixed pressure can also be set.

        # Get the inlet pressure [bar].
        p_in = self.get_foreign_state_value(components, 0)
        # Get the outlet pressure [bar].
        p_out = self.get_foreign_state_value(components, 1)

        # If the pressure difference is lower than 0.01 [bar], the specific
        # compression energy is zero
        if p_out - p_in < 0.01:
            spec_compression_work = 0
        else:
            # Get the compression ratio [-]
            p_ratio = p_out / p_in

            # Initial assumption for the polytropic exponent, value taken from MATLAB [-]
            n_initial = 1.6
            # Calculates the output temperature [K]
            temp_out = min(max(self.temp_in,
                               self.temp_in * p_ratio ** ((n_initial - 1) / n_initial)),
                           self.temp_in + 60)
            # Get temperature ratio [-]
            temp_ratio = temp_out / self.temp_in
            # Calculates the polytropic exponent [-]
            n = 1 / (1 - (log(temp_ratio) / log(p_ratio)))
            # Gets the compressibility factors of the hydrogen entering and
            # leaving the compressor [-]
            [z_in, z_out] = calculate_compressibility_factor(p_in, p_out, self.temp_in, temp_out)
            real_gas = (z_in + z_out) / 2
            # Specific compression work [kJ/kg]
            spec_compression_work = (
                (1 / self.efficiency) *
                self.R_H2 *
                self.temp_in *
                (n / (n - 1)) *
                ((((p_ratio) ** ((n - 1) / n))) - 1) *
                real_gas) / 1000

        # Convert specific compression work into electrical energy needed per kg H2 [Wh]
        self.spec_compression_energy = float(spec_compression_work / 3.6)

    def update_states(self, results, sim_params):
        # Update the states of the compressor

        # If the states dict of this object wasn't created yet, it's done here.
        if 'specific_compression_work' not in self.states:
            self.states['specific_compression_work'] = [None] * sim_params.n_intervals
        # self.states['inlet pressure'] = [None] * sim_params.n_intervals
        #  self.states['outlet pressure'] = [None] * sim_params.n_intervals
        return

        # self.states['specific_compression_work'][sim_params.i_interval] =
        # self.spec_compression_energy
