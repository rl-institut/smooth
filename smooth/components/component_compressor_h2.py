"""
This module represents a hydrogen compressor.

******
Scope
******
A hydrogen compressor is used in energy systems as a means of increasing
the pressure of hydrogen to suitable levels for feeding into other components
in the system or satisfying energy demands.

*******
Concept
*******
The hydrogen compressor is powered by electricity and intakes a low
pressure hydrogen flow while outputting a hgh pressure hydrogen flow.
The efficiency of the compressor is assumed to be 88.8%.

.. figure:: /images/hydrogen_compressor.png
    :width: 60 %
    :alt: hydrogen_compressor.png
    :align: center

    Fig.1: Simple diagram of a hydrogen compressor.

Specific compression energy
---------------------------
The specific compression energy is calculated by first obtaining the
compression ratio:

.. math::
    p_{ratio} = \\frac{p_{out}}{p_{in}}

* :math:`p_{ratio}` = compression ratio
* :math:`p_{out}` = outlet pressure [bar]
* :math:`p_{in}` = inlet pressure [bar]

Then the output temperature is calculated, and the initial assumption
for the polytropic exponent is assumed to be 1.6:

.. math::
    T_{out} = min(max(T_{in}, T_{in} \\cdot p_{ratio} ^ \\frac{n_{init} - 1}{n_{init}}),
    T_{in} + 60)

* :math:`T_{out}` = output temperature [K]
* :math:`T_{in}` = input temperature [K]
* :math:`n_{init}` = initial polytropic exponent

Then the temperature ratio is calculated:

.. math::
    T_{ratio} = \\frac{T_{out}}{T_{in}}

* :math:`T_{ratio}` = temperature ratio

Then the polytropic exponent is calculated:

.. math::
    n = \\frac{1}{1 - \\frac{log_{T_{ratio}}}{log_{p,ratio}}}

The compressibility factors of the hydrogen entering and leaving
the compressor is then calculated using interpolation considering
varying temperature, pressure and compressibility factor values
(see the calculate_compressibility_factor function). The real
gas compressibility factor is calculated using these two values
as follows:

.. math::
    Z_{real} = \\frac{Z_{in} + Z_{out}}{2}

* :math:`Z_{real}` = real gas compressibility factor
* :math:`Z_{in}` = compressibility factor on entry
* :math:`Z_{out}` = compressibility factor on exit

Thus the specific compression work is finally calculated:

.. math::
    c_{w_{1}} = \\frac{1}{\\mu} \\cdot R_{H_{2}} \\cdot T_{in} \\cdot \\frac{n}{n-1}
    \\cdot p_{ratio} ^ {(\\frac{n-1}{n} -1)} \\cdot \\frac{Z_{real}}{1000}

* :math:`c_{w_{1}}` = specific compression work [kJ/kg]
* :math:`\\mu` = compression efficiency
* :math:`R_{H_{2}}` = hydrogen gas constant

Finally, the specific compression work is converted into the amount of
electrical energy required to compress 1 kg of hydrogen:

.. math::
    c_{w_{2}} = \\frac{c_{w_{1}}}{3.6}

* :math:`c_{w_{2}}` = specific compression energy [Wh/kg]

"""


import oemof.solph as solph
from .component import Component
from .component_functions.component_functions import calculate_compressibility_factor
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
        self.bus_h2_in = None
        self.bus_h2_out = None
        self.bus_el = None
        self.m_flow_max = 33.6
        self.life_time = 20
        # It is assumed that hydrogen always enters the compressor at room temperature [K]
        # FIXME: An assumption from MATLAB is that hydrogen always enters the
        # compressor at this temp, should it be calculated instead of assumed??
        self.temp_in = 293.15
        # value taken from MATLAB
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

        self.current_vac = self.get_costs_and_art_costs()

    def create_oemof_model(self, busses, _):
        """Creates an oemof Transformer component using the information given in
        the CompressorH2 class, to be used in the oemof model

        :param busses: virtual buses used in the energy system
        :type busses: list
        :return: the oemof compressor component
        """
        compressor = solph.Transformer(
            label=self.name,
            inputs={
                busses[self.bus_h2_in]: solph.Flow(
                    nominal_value=self.m_flow_max * self.sim_params.interval_time / 60,
                    variable_cost=self.current_vac),
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
        :return: updated values for each state in the 'states' dict
        """
        # Update the states of the compressor

        # If the states dict of this object wasn't created yet, it's done here.
        if 'specific_compression_work' not in self.states:
            self.states['specific_compression_work'] = [None] * sim_params.n_intervals

        self.states['specific_compression_work'][sim_params.i_interval] \
            = self.spec_compression_energy
