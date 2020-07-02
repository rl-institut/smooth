import oemof.solph as solph
from .component import Component
from .component_functions.all_component_functions import calculate_compressibility_factor
from math import log


class CompressorH2(Component):
    """
    :param name: unique name given to the compressor component
    :type name: str
    :param bus_h2_in: lower pressure hydrogen bus that is an input of
        the compressor
    :type bus_h2_in: str
    :param bus_h2_out: higher pressure hydrogen bus that is the output
        of the compressor
    :type bus_h2_out: str
    :param bus_el: electric bus that is an input of the compressor
    :type bus_el: str
    :param m_flow_max: maximum mass flow through the compressor [kg/h]
    :type m_flow_max: float
    :param life_time: life time of the component [a]
    :type life_time: float
    :param temp_in: temperature of hydrogen on entry to the compressor [K]
    :type temp_in: float
    :param efficiency: overall efficiency of the compressor
    :type efficiency: float
    :param set_parameters(params): updates parameter default values
        (see generic Component class)
    :type set_parameters(params): function
    :param spec_compression_energy: specific compression energy
        (electrical energy needed per kg H2) [Wh/kg]
    :type spec_compression_energy: int
    :param R: gas constant (R) [J/(K*mol)]
    :type R: float
    :param Mr_H2: molar mass of H2 [kg/mol]
    :type Mr_H2: float
    :param R_H2: ToDo: define this properly

    """

    def __init__(self, params):
        """Constructor method
        """
        # Call the init function of th mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = 'Compressor_default_name'

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
        """Creates an oemof Transformer component using the information given in
        the Compressor H2 class, to be used in the oemof model

        :param busses: virtual buses used in the energy system
        :type busses list
        :return: the oemof compressor component
        """
        compressor = solph.Transformer(
            label=self.name,
            inputs={
                busses[self.bus_h2_in]: solph.Flow(
                    nominal_value=self.m_flow_max * self.sim_params.interval_time / 60),
                busses[self.bus_el]: solph.Flow()},
            outputs={busses[self.bus_h2_out]: solph.Flow()},
            conversion_factors={
                busses[self.bus_h2_in]: 1,
                busses[self.bus_el]: self.spec_compression_energy,
                busses[self.bus_h2_out]: 1})

        return compressor

    def prepare_simulation(self, components):
        """Prepares the simulation by calculating the specific compression energy

        :param components: list containing each component object
        :type components: list
        :return: the specific compression energy [Wh/kg]
        """
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
        """Updates the states in the compressor component

        :param results: oemof results object for the given time step
        :type results: object
        :param sim_params: simulation parameters for the energy system (defined by user)
        :type sim_params: object
        :return:
        """
        # Update the states of the compressor

        # If the states dict of this object wasn't created yet, it's done here.
        if 'specific_compression_work' not in self.states:
            self.states['specific_compression_work'] = [None] * sim_params.n_intervals

        self.states['specific_compression_work'][sim_params.i_interval] \
            = self.spec_compression_energy



