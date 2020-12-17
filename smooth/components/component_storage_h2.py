"""
This module represents a hydrogen storage tank.

*****
Scope
*****
Hydrogen can have a significant role in the integration of energy systems with
its storage capabilities. By providing a capacity for storing excess electricity
production, this can result in both the minimization of energy wasteage and
smaller scale energy production systems whilst meeting the same demand. This
is particularly important for cases of seasonal storage, where as an example,
excess electricity production in the summer months with the lowest demands
can be utilized at a later date.

*******
Concept
*******
The hydrogen storage component has a hydrogen bus input and a hydrogen bus
output, which will sometimes be different from each other if another
component in the system requires that the hydrogen has come directly from
the storage, for instance.

.. figure:: /images/h2_storage.png
    :width: 60 %
    :alt: h2_storage.png
    :align: center

    Fig.1: Simple diagram of a hydrogen storage.

Initial storage level
---------------------
The initial storage level is determined by the user through stating the
capacity and the initial storage factor in relation to the capacity:

.. math::
    SL_{init} = F_{SL,init} \\cdot C

* :math:`SL_{init}` = initial storage level [kg]
* :math:`F_{SL,init}` = initial storage level as a factor of the capacity [-]
* :math:`C` = storage capacity [kg]

Wanted storage level
--------------------
It is optional for the user to define a wanted storage level through the
storage level wanted factor (the default is set to None). If this value
has been defined, then there will be different artificial costs used
depending on whether the storage level is above or below the wanted level.

.. math::
    SL_{wanted} = F_{SL,wanted} \\cdot C

* :math:`SL_{wanted}` = wanted storage level [kg]
* :math:`F_{SL,wanted}` = wanted storage level as a factor of the capacity [-]
* :math:`C` = storage capacity [kg]

Mass and volume
---------------
The minimum storage level mass at minimum pressure and the volume of the
storage at maximum pressure are both calculated by initially using an iterative process
where the specific volume is changed. First the initial value for the specific
volume is given:

.. math::
    V_{spec,0} = 10

* :math:`V_{spec,0}` = predfined initial value for specific volume [m³/mol]

Then using the initial value, the iterative process begins:

.. math::
    V_{spec,i+1} = \\frac{R \\cdot T}{p + \\frac{rk_{a}}{T^{0.5}
    \\cdot V_{spec,i} \\cdot (V_{spec,i} + rk_{b})}} + rk_{b}

* :math:`V_{spec,i+1}` = ith + 1 specific volume [m³/mol]
* :math:`R` = gas constant [J/(K*mol)]
* :math:`T` = storage temperature [K]
* :math:`p` = storage pressure [Pa] (:math:`p_{min}` for calculating the mass
  and :math:`p_{max}` for the storage)
* :math:`rk_{a}` = Redlich Kwong equation of state parameter a
* :math:`V_{spec,i}` = ith specific volume [m³/mol]
* :math:`rk_{b}` = Redlich Kwong equation of state parameter b

After ten iterations, the specific volume value is used to obtain the storage volume
and the minimum storage level mass:

.. math::
    V = C \\cdot \\frac{V_{spec}}{M_{r}}

.. math::
    SL_{min} = V \\cdot \\frac{M_r}{V_{spec}}

* :math:`V` = storage volume [m³]
* :math:`C` = storage capacity [kg]
* :math:`V_{spec}` = specific volume [m³/mol]
* :math:`M_r` = molar mass of H2 [kg/mol]
* :math:`SL_{min}` = minimum storage level mass [kg]

Pressure
--------
The pressure of the storage is calculated as follows:

.. math::
    p = \\frac{R \\cdot T}{(V \\cdot \\frac{M_r}{SL} - rk_b)} -
    \\frac{rk_a}{T^{0.5} \\cdot V \\cdot \\frac{M_r}{SL}
    \\cdot (V \\cdot \\frac{M_r}{SL} + rk_b)}

* :math:`p` = storage pressure [Pa]
* :math:`SL` = storage level [kg]
"""

import oemof.solph as solph
from .component import Component
from oemof.outputlib import views


class StorageH2 (Component):
    """
    :param name: unique name given to the storage component
    :type name: str
    :param bus_in: hydrogen bus that enters the storage
    :type bus_in: str
    :param bus_out: hydrogen bus that leaves the storage
    :type bus_out: str
    :param p_min: minimum pressure of the storage [bar]
    :type p_min: numerical
    :param p_max: maximum pressure of the storage [bar]
    :type p_max: numerical
    :param storage_capacity: storage capacity at maximum pressure
        (usable storage + minimum storage) [kg]
    :type storage_capacity: numerical
    :param life_time: lifetime of the component [a]
    :type life_time: numerical
    :param initial_storage_factor: initial storage level as a factor
        of the capacity [-] e.g. 0.5 means half of the capacity
    :type initial_storage_factor: numerical
    :param delta_max: maximum chargeable hydrogen in one time step [kg/t] where
        t is the step-size
    :type delta_max: numerical
    :param slw_factor: storage level wanted as a factor of the capacity [-]
    :type slw_factor: numerical
    :param vac_in: normal variable artificial costs for charging (in) the
        storage [EUR/kg]
    :type vac_in: numerical
    :param vac_out: normal variable artificial costs for discharging (out) the
        storage [EUR/kg]
    :type vac_out: numerical
    :param vac_low_in: variable artificial costs for charging that apply if
        the storage level is below the wanted storage level [EUR/kg]
    :type vac_low_in: numerical
    :param vac_low_out: variable artificial costs for discharging that apply if
        the storage level is below the wanted storage level [EUR/kg]
    :type vac_low_out: numerical
    :param set_parameters(params): updates parameter default values (see generic Component class)
    :type set_parameters(params): function
    :param storage_level_init: initial storage level [kg]
    :type storage_level_init: numerical
    :param T_crit: critical temperature [K]
    :type T_crit: numerical
    :param p_crit: critical pressure [Pa]
    :type p_crit: numerical
    :param Mr: molar mass of H2 [kg/mol]
    :type Mr: numerical
    :param R: gas constant [J/(K*mol)]
    :param rk_a: Redlich Kwong equation of state parameter a
    :type rk_a: numerical
    :param rk_b: Redlich Kwong equation of state parameter b
    :type rk_b: numerical
    :param V: storage volume [m³]
    :type V: numerical
    :param storage_level_min: mass at minimum pressure that can't be used [kg]
    :type storage_level_min: numerical
    :param storage_level: storage level [kg]
    :type storage_level: numerical
    :param pressure: storage pressure [bar]
    :type pressure: numerical
    :param current_vac: current artificial costs for input and output [EUR/kg]
    :type current_vac: list
    """

    def __init__(self, params):
        """Constructor method
        """
        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = 'Storage_default_name'
        self.bus_in = None
        self.bus_out = None
        self.p_min = 0
        self.p_max = 450
        self.storage_capacity = 500
        self.life_time = 20
        self.initial_storage_factor = 0.5
        self.delta_max = None
        self.slw_factor = None

        # ------------------- PARAMETERS (VARIABLE ARTIFICIAL COSTS - VAC) -------------------
        self.vac_in = 0
        self.vac_out = 0
        self.vac_low_in = 0
        self.vac_low_out = 0

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)
        self.storage_level_init = self.initial_storage_factor * self.storage_capacity
        # If a storage level is set as wanted, the vac_low costs apply if the
        # storage is below that level [kg].
        if self.slw_factor is not None:
            self.storage_level_wanted = self.slw_factor * self.storage_capacity
        else:
            self.storage_level_wanted = None

        # ------------------- CONSTANTS FOR REAL GAS EQUATION -------------------
        self.T_crit = 33.19
        self.p_crit = 13.13 * 1e5
        self.Mr = 2.016 * 1e-3
        self.R = 8.314
        self.rk_a = 0.1428
        self.rk_b = 1.8208e-5

        # ----- FURTHER STORAGE VALUES DEPENDANT ON THE PRESSURE/CAPACITY -----
        self.V = self.get_volume(self.p_max, self.storage_capacity)
        self.storage_level_min = self.get_mass(self.p_min)
        # Asserts that the initial storage level must be greater than the minimum storage
        # level
        assert self.storage_level_init >= self.storage_level_min

        # ------------------- STATES -------------------
        self.storage_level = min(self.storage_level_init, self.storage_capacity)
        self.pressure = self.get_pressure(self.storage_level)

        # ------------------- VARIABLE ARTIFICIAL COSTS -------------------
        self.current_vac = [0, 0]

    def prepare_simulation(self, components):
        """Prepares the simulation by setting the appropriate artificial costs and
        the maximum chargeable hydrogen in one time step (delta max).

        :param components: List containing each component object
        :type components: list
        :return: artificial costs and delta max
        """
        # Set the var. art. costs.
        vac_in = self.vac_in
        vac_out = self.vac_out

        if self.storage_level_wanted is not None and self.storage_level < self.storage_level_wanted:
            # If a wanted storage level is set and the storage level fell below
            # that wanted level, the low VAC apply.
            vac_in = self.vac_low_in
            vac_out = self.vac_low_out

        self.current_vac = [vac_in, vac_out]
        self.delta_max = self.storage_capacity

    def create_oemof_model(self, busses, _):
        """Creates an oemof Generic Storage component from the information given in
        the StorageH2 class, to be used in the oemof model.

        :param busses: List of the virtual buses used in the energy system
        :type busses: list
        :return: The 'storage' oemof component
        """
        storage = solph.components.GenericStorage(
            label=self.name,
            outputs={busses[self.bus_out]: solph.Flow(
                nominal_value=self.delta_max, variable_costs=self.current_vac[1])},
            inputs={busses[self.bus_in]: solph.Flow(
                nominal_value=self.delta_max, variable_costs=self.current_vac[0])},
            initial_storage_level=self.storage_level / self.storage_capacity,
            nominal_storage_capacity=self.storage_capacity,
            min_storage_level=self.storage_level_min / self.storage_capacity,
            balanced=False)
        return storage

    def update_states(self, results, sim_params):
        """Updates the states of the storage component for each time step

        :param results: oemof results for the given time step
        :type results: object
        :param sim_params: simulation parameters for the energy system (defined by user)
        :type sim_params: object
        :return: updated state values for each state in the 'state' dict
        """
        data_storage = views.node(results, self.name)
        df_storage = data_storage['sequences']

        # Loop Through the data frame values and update states accordingly.
        for i_result in df_storage:
            if i_result[1] == 'capacity':
                if 'storage_level' not in self.states:
                    # Initialize an array that tracks the state stored mass.
                    self.states['storage_level'] = [None] * sim_params.n_intervals
                    self.states['pressure'] = [None] * sim_params.n_intervals
                # Check if this result is the storage capacity.
                self.storage_level = df_storage[i_result][0]
                self.states['storage_level'][sim_params.i_interval] = self.storage_level
                # Get the storage pressure [bar].
                self.pressure = self.get_pressure(self.storage_level)
                self.states['pressure'][sim_params.i_interval] = self.pressure

    def get_mass(self, p, V=None):
        """Calculates the mass of the storage at a certain pressure.

        :param p: pressure [bar]
        :type p: numerical
        :param V: storage volume [m³]
        :type V: numerical
        :return: mass of the storage [kg]
        """
        if V is None:
            V = self.V

        # If p_min is set to 0, the whole capacity should be usable, thus m will be zero as well.
        if V > 0 and p == 0:
            return 0

        # Storage temperature [K].
        T = 273.15 + 25
        # Convert pressure from bar to Pa [Pa].
        p = p * 1e5
        # The mass has to be defined in an iterative process by changing the spec. volume [m³/mol].
        v_spec = 10
        for i in range(10):
            v_spec = (
                self.R * T / (p + (self.rk_a / (T**0.5 * v_spec * (v_spec + self.rk_b))))
            ) + self.rk_b

        # Calculate the mass [kg].
        m = V * self.Mr / v_spec
        return m

    def get_volume(self, p, m):
        """Calculates the volume needed to fit a certain mass at given pressure.

        :param p: pressure [bar]
        :type p: numerical
        :param m: mass [kg]
        :type m: numerical
        :return: volume of the storage [m³]
        """

        # Storage temperature [K].
        T = 273.15 + 25
        # Convert pressure from bar to Pa [Pa].
        p = p * 1e5
        # The mass has to be defined in an iterative process by changing the spec. volume [m³/mol].
        v_spec = 10
        for i in range(10):
            v_spec = (
                self.R * T / (p + (self.rk_a / (T**0.5 * v_spec * (v_spec + self.rk_b))))
            ) + self.rk_b

        # Calculate the volume [m3]
        V = m * v_spec / self.Mr
        return V

    def get_pressure(self, m):
        """Calculates the storage pressure for a given mass.

        :param m: mass [kg]
        :type m: numerical
        :return: pressure [bar]
        """
        # Storage volume [m³].
        V = self.V
        # Storage temperature [K].
        T = 273.15 + 25
        # Calculate the storage pressure [Pa].
        p = self.R * T / (V * self.Mr / m - self.rk_b) - \
            self.rk_a / (T**0.5 * V * self.Mr / m * (V * self.Mr / m + self.rk_b))
        return p / 1e5
