import oemof.solph as solph
from smooth.components.component import Component
import numpy as np
from scipy import interpolate
from math import log


# Function for CompressorH2 component in order to calculate compressibility factor
def calculate_compressibility_factor(p_in, p_out, temp_in, temp_out):
    temp = np.transpose([200, 300, 400, 500, 600, 800, 1000, 2000])

    p = [1, 10, 20, 40, 60, 80, 100, 200, 400, 600, 800, 1000]

    z = [[1.0007, 1.0066, 1.0134, 1.0275, 1.0422, 1.0575, 1.0734, 1.163, 1.355, 1.555, 1.753, 1.936],
         [1.0005, 1.0059, 1.0117, 1.0236, 1.0357, 1.0479, 1.0603, 1.124, 1.253, 1.383, 1.510, 1.636],
         [1.0004, 1.0048, 1.0096, 1.0192, 1.0289, 1.0386, 1.0484, 1.098, 1.196, 1.293, 1.388, 1.481],
         [1.0004, 1.0040, 1.0080, 1.0160, 1.0240, 1.0320, 1.0400, 1.080, 1.159, 1.236, 1.311, 1.385],
         [1.0003, 1.0034, 1.0068, 1.0136, 1.0204, 1.0272, 1.0340, 1.068, 1.133, 1.197, 1.259, 1.320],
         [1.0002, 1.0026, 1.0052, 1.0104, 1.0156, 1.0208, 1.0259, 1.051, 1.100, 1.147, 1.193, 1.237],
         [1.0002, 1.0021, 1.0042, 1.0084, 1.0126, 1.0168, 1.0209, 1.041, 1.080, 1.117, 1.153, 1.187],
         [1.0009, 1.0013, 1.0023, 1.0044, 1.0065, 1.0086, 1.0107, 1.021, 1.040, 1.057, 1.073, 1.088]]

    interp_func = interpolate.interp2d(p, temp, z)

    z_in = interp_func(p_in, temp_in)
    z_out = interp_func(p_out, temp_out)

    return [z_in, z_out]


class CompressorH2(Component):
    def __init__(self, params):
        # Call the init function of th mother class.
        Component.__init__(self)

        """ PARAMETERS """
        self.name = 'Compressor_default_name'

        # Busses
        self.bus_h2_in = None
        self.bus_h2_out = None
        self.bus_el = None

        # Max. mass flow [kg/h].
        self.m_flow_max = 33.6

        # Life time [a].
        self.life_time = 20

        # ISSUE: An assumption from MATLAB is that hydrogen always enters the compressor at this temp, should it be
        # calculated instead of assumed??
        self.temp_in = 293.15

        # Overall efficiency of the compressor (value taken from MATLAB) [-]
        self.efficiency = 0.88829

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

        """ ENERGY NEED FOR COMPRESSION """
        # Specific compression energy (electrical energy needed per kg H2) [Wh/kg].
        self.spec_compression_energy = None
        # self.p_in = None
        # self.p_out = None

        """ CONSTANT PARAMETERS """
        # Mr_H2 = Molar mass of H2 [kg/mol], R = the gas constant (R) [J/(K*mol)]
        self.R = 8.314
        self.Mr_H2 = 2.016 * 1e-3
        self.R_H2 = self.R / self.Mr_H2

    def create_oemof_model(self, busses, _):
        compressor = solph.Transformer(
            label=self.name,
            inputs={
                busses[self.bus_h2_in]: solph.Flow(
                    nominal_value=self.m_flow_max * self.sim_params.interval_time / 60),
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

        # If the pressure difference is lower than 0.01 [bar], the specific compression energy is zero
        if p_out - p_in < 0.01:
            spec_compression_work = 0
        else:
            # Get the compression ratio [-]
            p_ratio = p_out / p_in

            # ISSUE: is this an assumption for the polytropic exponent??
            n_initial = 1.6

            temp_out = min(max(self.temp_in, self.temp_in * p_ratio ** ((n_initial - 1) / n_initial)),
                           self.temp_in + 60)
            temp_ratio = temp_out / self.temp_in

            n = 1 / (1 - (log(temp_ratio) / log(p_ratio)))

            [z_in, z_out] = calculate_compressibility_factor(p_in, p_out, self.temp_in, temp_out)

            real_gas = (z_in + z_out) / 2

            # Specific compression work [kJ/kg]
            spec_compression_work = ((1 / self.efficiency) * self.R_H2 * self.temp_in * (n / (n - 1)) *
                                     ((((p_ratio) ** ((n - 1) / n))) - 1) * real_gas) / 1000

        # Convert specific compression work into electrical energy needed per kg H2 [Wh]
        self.spec_compression_energy = float(spec_compression_work / 3.6)

    # self.p_in = p_in
    # self.p_out = p_out

    def update_states(self, results, sim_params):
        # Update the states of the compressor

        # If the states dict of this object wasn't created yet, it's done here.
        if not 'specific_compression_work' in self.states:
            self.states['specific_compression_work'] = [None] * sim_params.n_intervals
        # self.states['inlet pressure'] = [None] * sim_params.n_intervals
        #  self.states['outlet pressure'] = [None] * sim_params.n_intervals

        self.states['specific_compression_work'][sim_params.i_interval] = self.spec_compression_energy

