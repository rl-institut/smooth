from oemof.outputlib import views
import oemof.solph as solph
from .component import Component
import math
import numpy as np
import warnings

class Electrolyzer (Component):
    """Electrolyzer agents are created through this class

    :param name: unique name of the component
    :type name: str
    :param bus_el: name of the electric bus
    :type bus_el: str
    """
    def __init__(self, params):
        '''Constructor method
        '''
        # Call the init function of the mother class.
        Component.__init__(self)

        """ PARAMETERS """
        self.name = 'Electrolyzer_default_name'

        # Define the busses.
        self.bus_el = None
        self.bus_h2 = None

        # Max. power [W].
        self.power_max = 100000

        # pressure of hydrogen in the system in [Pa]
        self.pressure = 40 * 10**5
        # foreign state pressure parameter for compressor component [bar] (could be improved)
        self.fs_pressure = self.pressure/10**5
        # Initial temperature [K].
        self.temp_init = 273.15 + 25
        # Life time [a].
        self.life_time = 20

        """ PARAMETERS (SPECIFIC) """
        # The fitting parameter exchange current density [A/cm²].
        self.fitting_value_exchange_current_density = 1.4043839e-3
        # The thickness of the electrolyte layer [cm].
        self.fitting_value_electrolyte_thickness = 0.2743715938
        # Min. temperature of the electrolyzer (completely cooled down) [K].
        self.temp_min = 293.15
        # Highest temperature the electrolyzer can be [K].
        self.temp_max = 353.15
        # Maximal current density given by the manufacturer [A/cm^2].
        self.cur_dens_max = 0.4
        # Current density at which the maximal temperature is reached [A/cm^2].
        self.cur_dens_max_temp = 0.35
        # size of cell surface [cm²].
        self.area_cell = 1500

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)
        # Interval time [min].
        self.interval_time = self.sim_params.interval_time
        # Calculate the max. energy the electrolyzer can use in one time step [Wh].
        self.energy_max = self.power_max * self.interval_time/60

        """  CONSTANT PARAMETERS (PHYSICS) """
        # Faraday constant F [As/mol].
        self.faraday = 96485
        # Gas constant R [J /(mol K)].
        self.gas_const = 8.3144621
        # Moles of electrons needed to produce a mole of hydrogen[-].
        self.n = 2
        # Molar mass M_H2 [g / mol].
        self.molarity = 2.01588
        # Molar concentration of the KOH solution (10 mol/l for 28 wt% KOH) [mol/l].
        self.molarity_KOH = 10
        # Molal concentration of the KOH solution (7.64 mol/kg for 30 wt% KOH) [mol/kg].
        self.molality_KOH = 7.64
        # upper heating value in [MJ / kg]
        self.upp_heat_val = 141.8

        # Number of cell amount on one stack.
        # TO MAKE IT POSSIBLE TO DEFINE A MAX. POWER OF THE ELECTROLYZER, THE NUMBER OF CELLS ARE ADJUSTED ACCORDINGLY.
        # THIS IS DONE BY CHECKING HOW MANY CELLS LEAD TO THE MAX. POWER AT HIGHEST TEMPERATURE.
        self.z_cell = 1
        is_z_cell_found = False
        while not is_z_cell_found:
            this_curr_den = self.get_electricity_by_power(self.power_max/1000, self.temp_max)

            if this_curr_den is not None and this_curr_den < self.cur_dens_max:
                is_z_cell_found = True
            else:
                self.z_cell += 1

        # Max. hydrogen that can be produced in one time step [kg].
        self.max_production_per_step = self.cur_dens_max * self.area_cell * self.interval_time * 60 * self.z_cell / \
            (2 * self.faraday) * self.molarity / 1000

        """ STATES """
        # Temperature of the electrolyzer [K].
        self.temperature = self.temp_init
        # Tracking supporting points to calculate temperature later on.
        self.supporting_points = {}

    def conversion_fun_ely(self, ely_energy):
        # Create a function that will give out the mass values for the energy values at the breakpoints.

        # Check the index of this ely_energy entry.
        this_index = self.supporting_points['energy'].index(ely_energy)
        # Return the according hydrogen production value [kg].
        return self.supporting_points['h2_produced'][this_index]

    def create_oemof_model(self, busses, _):
        # Get the non-linear behaviour.
        self.update_nonlinear_behaviour()

        # Create the non-linear oemof component.
        electrolyzer = solph.custom.PiecewiseLinearTransformer(
            label=self.name,
            inputs={busses[self.bus_el]: solph.Flow(
               nominal_value=self.energy_max,
               variable_costs=0)},
            outputs={busses[self.bus_h2]: solph.Flow()},
            in_breakpoints=self.supporting_points['energy'],
            conversion_function=self.conversion_fun_ely,
            pw_repn='CC')
        return electrolyzer

    def update_nonlinear_behaviour(self):
        # Set up the breakpoints for the electrolyzer conversion of electricity to hydrogen.
        n_supporting_point = 10
        # Get the breakpoint values for electric energy [Wh] and produced hydrogen [kg].
        bp_ely_energy = []
        bp_ely_h2 = []
        bp_ely_temp = []
        for i_supporting_point in range(n_supporting_point + 1):
            # Calculate the energy for this breakpoint [Wh].
            this_energy = i_supporting_point / n_supporting_point * self.energy_max
            bp_ely_energy.append(this_energy)
            # Calculate the hydrogen produced [kg] and resulting temperature [K] with the energy of this breakpoint
            # and at the current temperature.
            [this_mass, this_temp] = self.get_mass_and_temp(this_energy / 1000)
            bp_ely_h2.append(this_mass)
            bp_ely_temp.append(this_temp)

        self.supporting_points['temperature'] = bp_ely_temp
        self.supporting_points['h2_produced'] = bp_ely_h2
        self.supporting_points['energy'] = bp_ely_energy

    def get_mass_and_temp(self, energy_used):
        # Calculate the mass produced and the resulting electrolyzer for a certain energy.
        # Parameter:
        #  energy_used: Energy value for the next time step [kWh].

        # Convert energy to power [kW]
        power = energy_used / (self.interval_time / 60)
        # Update voltage, current, current density and power in an iterative process.
        cur_dens = self.get_electricity_by_power(power)
        # Check if the current density is above the max. allowed value.
        if cur_dens > self.cur_dens_max:
            warnings.warn("Electrolyzer bought more electricity than it can use.")
            # Update current density to max. allowed value
            cur_dens = self.cur_dens_max

        # Calculate the resulting temperature [K]
        new_ely_temp = self.get_cell_temp(cur_dens)
        # Calculate the hydrogen produced [kg].
        h2_produced = self.get_mass_produced_by_current_state(cur_dens)
        # Return the produced hydrogen [kg] and the resulting electrolyzer temperature [K].
        return [h2_produced, new_ely_temp]

    def get_mass_produced_by_current_state(self, cur_dens):
        # Calculate the mass produced by a given current density.
        # Parameters:
        #  cur_dens: Given current density [A/cm²].

        # Get the current [A].
        current = cur_dens * self.area_cell
        # Calculate the hydrogen produced [kg]
        h2_production = current * (self.interval_time * 60 * self.z_cell / (2 * self.faraday) * self.molarity / 1000)
        # Return the mass produced
        return h2_production

    def get_cell_temp(self, cur_dens):
        # Calculate the electrolyzer temperature for the next time step.
        # Parameters:
        #  cur_dens: Given current density [A/cm²].

        # Check if current density is higher than the given density at the highest possible temperature. If so,
        # set the current density to its maximum.
        if cur_dens > self.cur_dens_max_temp:
            cur_dens_now = self.cur_dens_max_temp
        else:
            cur_dens_now = cur_dens

        # Save the temperature calculated one step before.
        temp_before = self.temperature
        # Calculate the temperature to which the electrolyzer is heating up depending on the given current density.
        # Lin. interpolation
        temp_aim = self.temp_min + (self.temp_max - self.temp_min) * cur_dens_now / self.cur_dens_max_temp
        # Calculate the new temperature of the electrolyzer by Newtons law of cooling. The exponent (-t[s]/2310) was
        # parameterized such that the 98 % of the temperature change are reached after 2.5 hours.
        temp_new = temp_aim + (temp_before - temp_aim) * math.exp(-self.interval_time*60 / 2310)
        # Return the new electrolyzer temperature [K].
        return temp_new

    def get_electricity_by_power(self, power, this_temp=None):
        # Calculate the current density for a given power.
        # Parameters:
        #  power: Current power the electrolyzer is operated with [kW].
        #  this_temp: Temperature of the electrolyzer [K].

        if this_temp is None:
            this_temp = self.temperature

        # The total electrolysis voltage consists out of three different voltage parts (u_act, u_ohm, u_ref).
        # If the current isn't given an iteration is needed to get the total voltage.
        # This is the tolerance within the el. power is allowed to differ as a result of the iteration.
        relative_error = 1e-5
        # Create a dummy for the power calculated within the iteration.
        power_iteration = 0
        # Create a dummy for the voltage calculated within the iteration.
        voltage_iteration = 0
        # Set an initial guess for the electrolyzer efficiency [-]
        initial_guess_for_efficiency = 0.65
        # Estimate the current density through the chemical power to start the iteration [A/cm²].
        cur_dens_iteration = (power * initial_guess_for_efficiency * 2.0 * self.faraday) / (
                self.area_cell * self.z_cell * self.molarity * self.upp_heat_val)
        # Calculate the current for the iteration start [A].
        current_iteration = cur_dens_iteration * self.area_cell
        # Determine the power deviation between the power target and the power reach within the iteration [kW].
        power_deviation = abs(power_iteration - power)
        # Execute the iteration until the power deviation is within the relative error which means the deviation is
        # accepted.
        i_run = 0
        while power_deviation > relative_error:
            # Calculate the voltage existing of three different parts [V].
            v_rev = (self.ely_voltage_u_rev(this_temp))
            v_act = (self.ely_voltage_u_act(cur_dens_iteration, this_temp))
            v_ohm = (self.ely_voltage_u_ohm(cur_dens_iteration, this_temp))
            # Get the voltage for this iteration step [V].
            voltage_iteration = (v_rev + v_act + v_ohm) * self.z_cell
            # For bad initial guesses, here a non-real number might appear.
            if not np.isreal(voltage_iteration) or i_run > 1000:
                return None

            # Get the power for this iteration step [kW].
            power_iteration = voltage_iteration * current_iteration / 1000
            # Get the current for this iteration step [A].
            current_iteration = power / voltage_iteration * 1000
            # Get the current density for this iteration step [A/cm²].
            cur_dens_iteration = current_iteration / self.area_cell
            # Calculate the new power deviation [kW].
            power_deviation = abs(power_iteration - power)
            # Increment the running variable.
            i_run += 1

        # Return the current density [A/cm²].
        return cur_dens_iteration

    def ely_voltage_u_act(self, cur_dens, temp):
        # This voltage part describes the activity losses within the electolyser.
        # Source: 'Modeling an alkaline electrolysis cell through reduced-order and loss estimate approaches'
        # from Milewski et al. (2014)!
        # Parameter:
        #  cur_dens: Current density [A/cm²]
        #  temp: Temperature [K]

        j0 = self.fitting_value_exchange_current_density

        '# COMPUTATION FOR EACH NODE'
        # The temperature of this loop run[K].
        this_temp = temp
        # The "alpha" values are valid for Ni - based electrodes.
        alpha_a = 0.0675 + 0.00095 * this_temp
        alpha_c = 0.1175 + 0.00095 * this_temp
        # The two parts of the activation voltage for this node[V].
        u_act_a = 2.306 * (self.gas_const * this_temp) / (self.n * self.faraday * alpha_a) * math.log10(cur_dens / j0)
        u_act_c = 2.306 * (self.gas_const * this_temp) / (self.n * self.faraday * alpha_c) * math.log10(cur_dens / j0)
        # The activation voltage for this node[V].
        voltage_activation = u_act_a + u_act_c

        return voltage_activation

    def ely_voltage_u_ohm(self, cur_dens, temp):
        # This model takes into account two ohmic losses, one being the resistance of the electrolyte itself
        # (resistanceElectrolyte) and other losses like the presence of bubbles (resistanceOther).
        # Source: 'Modeling an alkaline electrolysis cell through reduced-order and loss estimate approaches'
        # from Milewski et al. (2014)
        # Parameter:
        #  cur_dens: Current density [A/cm²]
        #  temp: Temperature [K]

        electrolyte_thickness = self.fitting_value_electrolyte_thickness

        # Temperature of this loop run [K].
        this_temp = temp
        # The conductivity of the the potassium hydroxide (KOH) solution [1/(Ohm*cm)].
        conductivity_electrolyte = -2.041 * self.molarity_KOH - 0.0028 * self.molarity_KOH ** 2 + 0.001043 * \
                                   self.molarity_KOH ** 3 + 0.005332 * self.molarity_KOH * this_temp + 207.2 * \
                                   self.molarity_KOH / this_temp - 0.0000003 * self.molarity_KOH ** 2 * this_temp ** 2
        # The electrolyte resistance [Ohm*cm²].
        resistance_electrolyte = electrolyte_thickness / conductivity_electrolyte
        # Void fraction of the electrolyte (j is multiplied by 10^4 because the units the formula is made for is A/m²
        # and j is in A/cm²) [-].
        epsilon = 0.023 * 2 / 3 * (cur_dens * 10 ** 4) ** 0.3
        # The conductivity of bubbles and other effects [1/(Ohm*cm)].
        conductivity_other = (1 - epsilon) ** 1.5 * conductivity_electrolyte
        # Computing the resistance of bubbles in the electrolyte and other effects [Ohm*cm²].
        resistance_other = electrolyte_thickness / conductivity_other
        # Total ohmic resistance [Ohm*cm²].
        resistance_total = resistance_electrolyte + resistance_other
        # Cell voltage loss due to ohmic resistance [V].
        # (j is the current density with the unit A/cm²).
        voltage_ohm = resistance_total * cur_dens
        return voltage_ohm

    def ely_voltage_u_rev(self, temp):
        # The reversible voltage can be calculated by two parts, one takes into account changes of the reversible cell
        # voltage due to temperature changes, the second part due to pressure changes.
        # Source: 'Modeling an alkaline electrolysis cell through reduced-order and loss estimate approaches'
        # from Milewski et al. (2014)
        # This calculations are valid in a temperature range from 0°C - 250°C, a pressure range from 1 bar - 200 bar and
        # a concentration range from 2 mol/kg - 18 mol/kg.
        # Parameter:
        #  temp: Temperature [K]

        # Coefficient 1 for the vapor pressure of the KOH solution.
        c1 = -0.0151 * self.molality_KOH - 1.6788e-03 * self.molarity_KOH ** 2 + 2.2588e-05 * self.molality_KOH ** 3
        # Coefficient 2 for the vapor pressure of the KOH solution.
        c2 = 1.0 - 1.2062e-03 * self.molality_KOH + 5.6024e-04 * self.molality_KOH ** 2 - 7.8228e-06 * self.molality_KOH**3

        '# COMPUTATION FOR ALL REQUESTED TEMPERATURES'
        # Get the temperature for this loop run [K].
        this_temp = temp
        # Compute the part of the reversible cell voltage that changes due to temperature [V].
        voltage_temperature = 1.5184 - 1.5421e-03 * this_temp + 9.526e-05 * this_temp * math.log(this_temp) + 9.84e-08 \
                              * this_temp ** 2
        # Calculate the vapor pressure of water [bar].
        pressure_water = math.exp(81.6179 - 7699.68 / this_temp - 10.9 * math.log(this_temp) + 9.5891e-03 * this_temp)
        # Calculate the vapor pressure of KOH solution [bar].
        pressure_koh = math.exp(2.302 * c1 + c2 * math.log(pressure_water))
        # Calculate the water activity value.
        water_activity = math.exp(
            -0.05192 * self.molality_KOH + 0.003302 * self.molality_KOH ** 2 + (3.177 * self.molality_KOH -
                                                                            2.131 * self.molality_KOH ** 2) / this_temp)
        # Compute the part of the reversible cell voltage that changes due to pressure [V].
        voltage_pressure = self.gas_const * this_temp / (self.n * self.faraday) *\
                    math.log((self.pressure - pressure_koh) * (self.pressure - pressure_koh) ** 0.5 / water_activity)
        # Calculate the reversible voltage [V].
        voltage_reversible = voltage_temperature + voltage_pressure

        return voltage_reversible

    def update_states(self, results, sim_params):
        # Update the states of the electrolyzer

        # If the states dict of this object wasn't created yet, it's done here.
        if not 'temperature' in self.states:
            self.states['temperature'] = [None] * sim_params.n_intervals

        # Get the flows of the electrolyzer for this time step.
        data_electrolyzer = views.node(results, self.name)
        df_electrolyzer = data_electrolyzer['sequences']

        # Get the hydrogen produced this time step [kg].
        for i_result in df_electrolyzer:
            if i_result[0][0] == self.name and i_result[1] == 'flow':
                # Case: This is the flow from the electrolyzer to the hydrogen bus, therefor the produced H2 [kg].
                this_h2_produced = df_electrolyzer[i_result][0]

        # With the hydrogen produced this step the according temperature can be interpolated from the supporting points.
        suporting_points_temp = self.supporting_points['temperature']
        suporting_points_h2 = self.supporting_points['h2_produced']
        this_temp = np.interp(this_h2_produced, suporting_points_h2, suporting_points_temp)

        # Update the current temperature and the temperature state for this time step.
        self.temperature = this_temp
        self.states['temperature'][sim_params.i_interval] = this_temp





