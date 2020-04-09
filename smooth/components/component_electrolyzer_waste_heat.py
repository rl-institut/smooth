from oemof.outputlib import views
import oemof.solph as solph
from .component_electrolyzer import Electrolyzer
import math
import numpy as np
import warnings
import pyomo.environ as po

class ElectrolyzerWasteHeat (Electrolyzer):
    """ Electrolyzer agents with waste heat model are created through this subclass of the Electrolyzer class """
    def __init__(self, params):

        # Call the init function of the mother class.
        Electrolyzer.__init__(self)

        """ PARAMETERS """

        # resistance to heat transfer R_t [K/W]
        self.resistance_to_heat_transfer = 0.164
        # source: Dieguez et al., 'Thermal Performance of a commercial alkaline water electrolyzer: Experimental study
        # and mathematical modeling', Int. J. Hydrogen Energy, 2008

        """  CONSTANT PARAMETERS (PHYSICS) """
        # constant parameters for calculating sensible heat:
        # molar mass M_O2
        self.molar_mass_O2 = 31.99880
        # specific heat at constant pressure [J/(kg*K)]
        self.c_p_H2 = 14304
        self.c_p_O2 = 920
        self.c_p_H2O = 4183

        # Save the two models to set constraints later.
        self.model_h2 = None
        self.model_th = None


    def conversion_fun_thermal(self, ely_energy):
        # Create a function that will give out the thermal energy values for the electric energy values at the breakpoints.

        # Check the index of this ely_energy entry.
        this_index = self.supporting_points['energy'].index(ely_energy)
        # Return the according hydrogen production value [kg].
        return self.supporting_points['thermal_energy'][this_index]

    def create_oemof_model(self, busses, model):
        # Get the non-linear behaviour.
        self.update_nonlinear_behaviour()

        # First create the hydrogen producing oemof component
        electrolyzer = solph.custom.PiecewiseLinearTransformer(
            label=self.name,
            inputs={busses[self.bus_el]: solph.Flow(
               nominal_value=self.energy_max,
               variable_costs=0)},
            outputs={busses[self.bus_h2]: solph.Flow()},
            in_breakpoints=self.supporting_points['energy'],
            conversion_function=self.conversion_fun_ely,
            pw_repn='CC')

        # Then create the thermal oemof component.
        electrolyzer_thermal = solph.custom.PiecewiseLinearTransformer(
            label=self.name+'_thermal',
            inputs={busses[self.bus_el]: solph.Flow(
               nominal_value=self.energy_max,
               variable_costs=0)},
            outputs={busses[self.bus_th]: solph.Flow()},
            in_breakpoints=self.supporting_points['energy'],
            conversion_function=self.conversion_fun_thermal,
            pw_repn='CC')

        # Add the two components to the model.
        model.add(electrolyzer, electrolyzer_thermal)

        self.model_h2 = electrolyzer
        self.model_th = electrolyzer_thermal

        return None


    def update_nonlinear_behaviour(self):
        # Set up the breakpoints for the electrolyzer conversion of electricity to hydrogen.
        n_supporting_point = 10
        # Get the breakpoint values for electric energy [Wh] and produced hydrogen [kg].
        bp_ely_energy = []
        bp_ely_h2 = []
        bp_ely_temp = []
        bp_ely_thermal = []
        for i_supporting_point in range(n_supporting_point + 1):
            # Calculate the energy for this breakpoint [Wh].
            this_energy = i_supporting_point / n_supporting_point * self.energy_max
            bp_ely_energy.append(this_energy)
            # Calculate the hydrogen produced [kg] and resulting temperature [K] with the energy of this breakpoint
            # and at the current temperature.
            [this_mass, this_temp] = self.get_mass_and_temp(this_energy / 1000)
            bp_ely_h2.append(this_mass)
            bp_ely_temp.append(this_temp)
            # Calculate the waste heat [Wh] with the energy, hydrogen produced and resulting temperature of this
            # breakpoint at the current temperature.
            this_waste_heat = self.get_waste_heat(this_energy / 1000, this_mass, this_temp) * 1000 # [Wh]
            bp_ely_thermal.append(this_waste_heat)

        self.supporting_points['temperature'] = bp_ely_temp
        self.supporting_points['h2_produced'] = bp_ely_h2
        self.supporting_points['energy'] = bp_ely_energy
        self.supporting_points['thermal_energy'] = bp_ely_thermal


    def get_waste_heat(self, energy_used, h2_produced, new_ely_temp):
        # source: Dieguez et al., 'Thermal Performance of a commercial alkaline water electrolyzer: Experimental study
        # and mathematical modeling', Int. J. Hydrogen Energy, 2008
        # parameters:
        # energy_used [kWh], h2_produced [kg], new_ely_temp [K]
        # return value:
        # waste_heat [kWh]

        # waste heat is heat that is removed through cooling, cooling only takes place if the elctrolyzer is near to its
        # maximum temperature, factor 0.999 is chosen since newtons law of cooling describes an exponential convergency
        # towards the aimed temperature, therefore temperatures near the max. temperature are reached quite fast whereas
        # the max. temperature itself is reached after a longer period of time
        if new_ely_temp >= (0.999 * self.temp_max):
            # calcualting the internal heat generation out of the relation Q = E_el*(1-eta_stack) with eta_stack = m_H2
            # * HHV / E_el, eta_I (ac/dc conversion) is neglected for a first approximation
            internal_heat_generation = energy_used - h2_produced * self.upp_heat_val / 3.6  # [kWh]
            # heat losses modeled trough an overall convective-radiative heat transfer coeffiecient
            heat_losses = (new_ely_temp - self.temp_min) / (self.resistance_to_heat_transfer * 1000) \
                          * (self.interval_time / 60)  # [kWh]
            # sensible heat is calculated using water decomposition stoichiometry, mass balance and constant specific
            # heat, latent heat is neglected for a first approximation
            [sensible_heat, latent_heat] = self.sensible_and_latent_heats(h2_produced, new_ely_temp)  # [kWh]
            # the waste heat follows from the energy balance
            waste_heat = internal_heat_generation - heat_losses + sensible_heat
        else:
            waste_heat = 0
        return waste_heat


    def sensible_and_latent_heats(self, mass_H2, new_ely_temp):
        # mass of H2, O2 and H2O is related by the water decomposition stoichiometry and the mass balance
        mass_O2 = mass_H2 * 0.5 * self.molar_mass_O2 / self.molarity
        # as a first approximation mass_H2O_vapor is neglected in the mass balance, since condensers temperature and
        # pressure are not known
        mass_H2O = mass_H2 + mass_O2
        # sensible heat removed from the system with the H2 and O2 streams, as well as the sensible heat required to
        # warm the deionized water from room temperature to the stack operating temperature
        sensible_heat = (mass_H2O * self.c_p_H2O * (self.temp_min - new_ely_temp) \
                        - mass_H2 * self.c_p_H2 * (new_ely_temp - self.temp_min) \
                        - mass_O2 * self.c_p_O2 * (new_ely_temp - self.temp_min)) / 3.6e6 # [kWh], 1J = 1/3.6e6 kWh
        # latent heat is neglected since mass_H2O_vapor is neglected
        return [sensible_heat, 0]


    def update_constraints(self, busses, model_to_solve):
        # Set a constraint so that the electric inflow of the hydrogen producing and the thermal part are always the same (which
        # is necessary while the piecewise linear transformer cannot have two outputs yet and therefore the two parts
        # need to be separate components).
        def electrolyzer_ratio_rule(model, t):
            # Inverter flow
            expr = 0
            expr += model.flow[busses[self.bus_el], self.model_th, t]
            # force discharge to zero when grid available
            expr += - model.flow[busses[self.bus_el], self.model_h2, t]
            return (expr == 0)

        model_to_solve.electrolyzer_flow_ratio_fix = po.Constraint(model_to_solve.TIMESTEPS, rule=electrolyzer_ratio_rule)





