"""
This module is created as a subclass of the Electrolyzer module with the inclusion
of a waste heat model.

******
Scope
******
The significance of including the heat generation from an electrolyzer in an
energy system is that this heat can be utilized for other means (e.g.
contributing towards a heat demand) as opposed to wasted. This will be
particularly important with the implementation of large scale electrolyzers,
where there is the potential to recover large quantities of energy.

*INCLUDE FIGURE?

In this component, it is assumed that the electrolyzer consists of a cylindrical
cell stack along with two cylindrical gas separators. It is further assumed
that:

* The cell stack height consists of the cells plus two ends. The height of the
  end of the stack which is not part of the cells has a dependence on the diameter
  of the cell. The ratio is taken as 7:120 [1]
* The height of an individual cell is in a ratio of 1:75.5 with the cell
  diameter [2]
* The overall surface area exposed by the gas separators and the pipe
  communicating them is in a ratio of 1:0.42 with the surface area of the stack [3]

*******
Concept
*******
Waste heat
----------
The waste heat, which is removed from the electrolyzer by the cooling water,
is calculated using the following equation, based on [3]:

.. math::
    Q_W = Q_{gen} - Q_L + L + S

* :math:`Q_{W}` = waste heat
* :math:`Q_{gen}` = internal heat generation
* :math:`Q_{L}` = heat losses to the environment
* :math:`L` = latent heat
* :math:`S` = sensible heat

Internal heat generation
------------------------
The internal heat generation within an electrolyzer is as a result of a greater
energy supply to the electrolyzer than is thermodynamically required. This is
necessary for reaching high water electrolysis rates [3]. The internal heat
gemeration is calculated as follows:

.. math::
   Q_{gen} = E_{sup} - E_{H_{2}}

* :math:`E_{sup}` = total energy supply to the electrolyzer
* :math:`E_{H_{2}}` = the energy equivalent of the produced hydrogen

Heat losses
-----------
In order to calculate the heat losses to the environment, the heat transfer
coefficient is first calculated based on [3]:

.. math::
  h = 1.32 * \\frac{\\Delta T}{d}^{0.25}

The heat losses are then calculated taking into consideration the heat
transfer coefficient, the total surface area of the main parts of the
electrolyzer (the cell stack and the gas separators) and the temperature
difference between the surface of the electrolyzer and the ambient temperature [3].
The equation is as follows:

.. math::
    Q_L = A_{sep} * h * (T_{sep} - T_{amb}) + A_{stack} * h * (T_{stack} - T_{amb})

* :math:`A_{sep}` = total surface area of the gas separators
* :math:`T_{sep}` = separator surface temperature
* :math:`T_{amb}` = ambient temperature
* :math:`A_{stack}` = total surface area of the cell stack
* :math:`T_{stack}` = cell stack surface temperature

Sensible and latent heat
------------------------

**Sensible heat** \n
The sensible heat removed from the system within the :math:`H_2` and :math:`O_2` streams,
as well as the sensible heat required to warm the deionized water from ambient
temperature to the stack operating temperature, must be considered when determining
the total waste heat. From the known mass of produced hydrogen along with the
molar masses of :math:`H_2` and :math:`O_2`, the mass of produced oxygen is
determined:

.. math::
    m_{O_{2}} = m_{H_{2}} * 0.5 * \\frac{M_{O_{2}}}{M_{H_{2}}}

* :math:`m_{O_{2}}` = mass of oxygen stream
* :math:`m_{H_{2}}` = mass of hydrogen stream
* :math:`M_{O_{2}}` = molar mass of oxygen
* :math:`M_{H_{2}}` = molar mass of hydrogen

The mass of :math:`H_2O` is then determined as follows:

.. math::
    m_{H_{2O}} = m_{H_{2}} + m_{O_{2}}

* :math:`m_{H_{2O}}` = mass of water

Thus, the sensible heat is calculated using mass and specific heat:

.. math::
    S = \\frac{m_{H_{2}O} * c_{p_{H_{2}O}} *-\\Delta T - m_{H_{2}} * c_{p_{H_{2}} * \\Delta T + m_{O_{2}} * c_{p_{O_{2}} * \\Delta T}{3.6e6}

* :math:`c_{p_{H_{2}O}}` = specific heat of water
* :math:`\\Delta T` = the temperature change between the ambient and electrolyzer temperature
* :math:`c_{p_{H_{2}}}` = specific heat of hydrogen
* :math:`c_{p_{O_{2}}}` = specific heat of oxygen

**Latent heat** \n

The latent heat is neglected since the mass of :math:`H_{2O}` vapor is neglected.

References
----------
[1] De Silva, Y.S.K. (2017). Design of an Alkaline Electrolysis Stack, University of Agder.
[2] Vogt, U.F. et al. (2014). Novel Developments in Alkaline Water Electrolysis, Empa
Laboratory of Hydrogen and Energy.
[3] Dieguez, P.M. et al. (2008). Thermal Performance of a commercial alkaline water
electrolyser: Experimental study and mathematical modeling, Int. J. Hydrogen Energy.

"""

import oemof.solph as solph
from .component_electrolyzer import Electrolyzer
import pyomo.environ as po


class ElectrolyzerWasteHeat(Electrolyzer):
    """
    :param param_bus_th: inclusion of the thermal bus in the parameters dictionary,
        which was not included in the electrolyzer mother class
    :type param_bus_th: dict
    :param bus_th: thermal bus that is the output of the electrolyzer
    :type bus_th: str
    :param set_parameters(params): updates parameter default values (see generic Component class)
    :type set_parameters(params): function
    :param interval_time: interval time [min]
    :type interval_time: numerical
    :param energy_max: maximum energy that the electrolyzer can use in one time step [Wh]
    :type energy_max: numerical
    :param c_p_H2: specific heat of hydrogen at constant pressure [J/(kg*K)]
    :type c_p_H2: numerical
    :param c_p_O2: specific heat of oxygen at constant pressure [J/(kg*K)]
    :type c_p_O2: numerical
    :param c_p_H2O: specific heat of water at constant pressure [J/(kg*K)]
    :type c_p_H2O: numerical
    :param diameter_cell: diameter of the electrolyzer cell [m]
    :type diameter_cell: numerical
    :param stack_end_height: height of the two stack ends that are not part of the cells,
        from the perspective of the total stack height [m]
    :type stack_end_height: numerical
    :param height_cell: height of an individual cell in relation to the cell diameter [m]
    :type height_cell: numerical
    :param height_stack: total stack height, which is calculated by taking the cell stack
        plus the two additional ends of the stack into consideration [m]
    :type height_stack: numerical
    :param area_stack: external surface area of the electrolyser stack under the
        assumption that it is cylindrical [m^2]
    :type area_stack: numerical
    :param area_separator: overall surface area exposed by the gas separators and the
        pipe communicating them [m^2]
    :type area_separator: numerical
    :param model_h2: model created with regards to the hydrogen produced by the
        electrolyser
    :type model_h2: oemof model
    :param model_th: model created with regards to the thermal energy produced by
        the electrolyser
    :type model_th: oemof model

     """

    def __init__(self, params):
        """ Constructor method
        """
        # Split the params dict
        param_bus_th = {"bus_th": params.pop("bus_th")}

        # Call the init function of the mother class.
        Electrolyzer.__init__(self, params)

        # ------------------- PARAMETERS -------------------
        # Define the additional thermal bus
        self.bus_th = None

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(param_bus_th)
        # Interval time [min].
        self.interval_time = self.sim_params.interval_time
        # Calculate the max. energy the electrolyzer can use in one time step [Wh].
        self.energy_max = self.power_max * self.interval_time / 60

        # ------------------- CONSTANT PARAMETERS (PHYSICS) -------------------
        # constant parameters for calculating sensible heat:
        # specific heat at constant pressure [J/(kg*K)]
        self.c_p_H2 = 14304
        self.c_p_O2 = 920
        self.c_p_H2O = 4183

        # ------------------- ELECTROLYZER GEOMETRY PARAMETERS -------------------
        self.diameter_cell = (4 * self.area_cell / 3.14) ** 0.5 / 100  # m
        # The height of the end of the stack which is not part of the cells is assumed to have a
        # dependence on the diameter of the cell. The ratio is taken as 7 : 120
        # (stack_end_height : diameter_cell), which is based on De Silva, Y.S.K. (2017). Design
        # of an Alkaline Electrolysis Stack, University of Agder.
        self.stack_end_height = 0.058 * self.diameter_cell
        # The height of an individual cell in relation to cell diameter is calculated using example
        # data from Vogt, U.F. et al. (2014). Novel Developments in Alkaline Water Electrolysis,
        # Empa Laboratory of Hydrogen and Energy. The individual cell height is estimated and
        # compared with the given cell diameter, and a ratio of 1 : 75.5 is obtained.
        self.height_cell = self.diameter_cell / 75.5
        # The total stack height is calculated by taking the cell stack and the two ends of the
        # stack into consideration
        self.height_stack = (self.height_cell * self.z_cell) + (2 * self.stack_end_height)
        # The external surface area of the electrolysis stack is calculated assuming that it is
        # cylindrical
        self.area_stack = (
                2 * self.area_cell / 10000 + 3.14 * self.diameter_cell * self.height_stack
        )  # [m^2]
        # The overall surface area exposed by the gas separators and the pipe communicating
        # them is assumed to be in a ratio of 1 : 0.42 with the area of the stack (taken from
        # Dieguez et al)
        self.area_separator = 2.38 * self.area_stack

        # Save the two models to set constraints later.
        self.model_h2 = None
        self.model_th = None

    def conversion_fun_ely(self, ely_energy):
        """Gives out the mass values for the electric energy values at the breakpoints.

        :param ely_energy: The electric energy values at the breakpoints
        :type ely_energy: numerical
        :return: The according hydrogen production value [kg]
        """
        # Create a function that will give out the mass values for the electric energy
        # values at the breakpoints.

        # Check the index of this ely_energy entry.
        this_index = self.supporting_points["energy_halved"].index(ely_energy)
        # Return the according hydrogen production value [kg].
        return self.supporting_points["h2_produced"][this_index]

    def conversion_fun_thermal(self, ely_energy):
        """Gives out the thermal energy values for the electric energy values at the
        breakpoints.

        :param ely_energy: The electric energy values at the breakpoints
        :type ely_energy: numerical
        :return: The according thermal energy production value [Wh]
        """
        # Create a function that will give out the thermal energy values for the electric
        # energy values at the breakpoints.
        # Check the index of this ely_energy entry.
        this_index = self.supporting_points["energy_halved"].index(ely_energy)
        # Return the according hydrogen production value [kg].
        return self.supporting_points["thermal_energy"][this_index]

    def create_oemof_model(self, busses, model):
        """Creates two separate oemof Piecewise Linear Transformer components for the hydrogen
        and thermal production of the electrolyser from information given in the
        Electrolyser Waste Heat class, to be used in the oemof model

        :param busses: virtual buses used in the energy system
        :type busses: list
        :param model: oemof model containing the hydrogen production and thermal energy
            production of the electrolyser
        :type model: model
        :return: the oemof electrolyzer and electrolyzer thermal components
        """
        # Get the non-linear behaviour.
        self.update_nonlinear_behaviour()

        # First create the hydrogen producing oemof component
        electrolyzer = solph.custom.PiecewiseLinearTransformer(
            label=self.name,
            inputs={
                busses[self.bus_el]: solph.Flow(
                    nominal_value=self.energy_max / 2, variable_costs=0
                )
            },
            outputs={busses[self.bus_h2]: solph.Flow()},
            in_breakpoints=self.supporting_points["energy_halved"],
            conversion_function=self.conversion_fun_ely,
            pw_repn="CC",
        )

        # Then create the thermal oemof component.
        electrolyzer_thermal = solph.custom.PiecewiseLinearTransformer(
            label=self.name + "_thermal",
            inputs={
                busses[self.bus_el]: solph.Flow(
                    nominal_value=self.energy_max / 2, variable_costs=0
                )
            },
            outputs={busses[self.bus_th]: solph.Flow()},
            in_breakpoints=self.supporting_points["energy_halved"],
            conversion_function=self.conversion_fun_thermal,
            pw_repn="CC",
        )

        # Add the two components to the model.
        model.add(electrolyzer, electrolyzer_thermal)

        self.model_h2 = electrolyzer
        self.model_th = electrolyzer_thermal

        return None

    def update_nonlinear_behaviour(self):
        """Updates the nonlinear behaviour of the electrolyser in terms of hydrogen and
        thermal energy production, as well as the resulting temperature of the electrolyser.
        """
        # Set up the breakpoints for the electrolyzer conversion of electricity to hydrogen.
        n_supporting_point = 10
        # Get the breakpoint values for electric energy [Wh] and produced hydrogen [kg].
        bp_ely_energy = []
        bp_ely_h2 = []
        bp_ely_temp = []
        bp_ely_thermal = []
        for i_supporting_point in range(n_supporting_point + 1):
            # Calculate the energy for this breakpoint [Wh].
            this_energy = (
                    i_supporting_point / n_supporting_point * self.energy_max
            )
            bp_ely_energy.append(this_energy)
            # Calculate the hydrogen produced [kg] and resulting temperature [K] with the
            # energy of this breakpoint and at the current temperature.
            [this_mass, this_temp] = self.get_mass_and_temp(this_energy / 1000)
            bp_ely_h2.append(this_mass)
            bp_ely_temp.append(this_temp)
            # Calculate the waste heat [Wh] with the energy, hydrogen produced and resulting
            # temperature of this breakpoint at the current temperature.
            this_waste_heat = (
                    self.get_waste_heat(this_energy / 1000, this_mass, this_temp)
                    * 1000
            )  # [Wh]
            bp_ely_thermal.append(this_waste_heat)

        self.supporting_points["temperature"] = bp_ely_temp
        self.supporting_points["h2_produced"] = bp_ely_h2
        self.supporting_points["energy"] = bp_ely_energy
        self.supporting_points["thermal_energy"] = bp_ely_thermal
        self.supporting_points["energy_halved"] = [
            this_bp / 2 for this_bp in bp_ely_energy
        ]

    def get_waste_heat(self, energy_used, h2_produced, new_ely_temp):
        """Approximates waste heat production based on calculations of internal heat
        generation, heat losses to the environment and the sensible and latent
        heat removed from the system.

        #ToDo: put equations here or in the beginning?

        :param energy_used: The energy consumed by the electrolyser [kWh]
        :type energy_used: numerical
        :param h2_produced: The hydrogen produced by the electrolyser [kg]
        :type h2_produced: numerical
        :param new_ely_temp: The resulting temperature of the electrolyser [K]
        :type new_ely_temp: numerical
        :return: The resulting waste heat produced by the electrolyser [kWh]
        """
        # source: Dieguez et al., 'Thermal Performance of a commercial alkaline
        # water electrolyzer: Experimental study and mathematical modeling',
        # Int. J. Hydrogen Energy, 2008 energy_used [kWh] --> internal_heat_generation [kWh]
        internal_heat_generation = (
                energy_used - h2_produced * self.upp_heat_val * 1e6 / 3600 / 1000
        )  # [kWh]
        # heat losses:
        dT = new_ely_temp - self.temp_min  # [K]
        # equation from Dieguez et al:
        heat_transfer_coefficient = (
                1.32 * (dT / self.diameter_cell) ** 0.25
        )  # [W/(m^2*K)]

        heat_losses = (
                heat_transfer_coefficient
                * (self.area_stack + self.area_separator)
                * dT * self.interval_time / 60 / 1000)  # [kWh]
        [sensible_heat, latent_heat] = self.sensible_and_latent_heats(
            h2_produced, new_ely_temp
        )  # [kWh]
        if new_ely_temp >= (0.999 * self.temp_max):
            waste_heat = internal_heat_generation - heat_losses + sensible_heat
        else:
            waste_heat = 0
        return waste_heat

    def sensible_and_latent_heats(self, mass_H2, new_ely_temp):
        """Calculates the sensible and latent heat that has been removed with the
        hydrogen and oxygen streams leaving the system.

        :param mass_H2: The mass of hydrogen [kg]
        :type mass_H2: numerical
        :param new_ely_temp: The resulting temperature of the electrolyser [K]
        :type new_ely_temp: numerical
        :return: Values for the sensible and latent heat
        """
        # mass of H2, O2 and H2O is related by the water decomposition stoichiometry
        # and the mass balance
        mass_O2 = mass_H2 * 0.5 * self.molar_mass_O2 / self.molarity
        # as a first approximation mass_H2O_vapor is neglected in the mass balance,
        # since condensers temperature and pressure are not known
        mass_H2O = mass_H2 + mass_O2
        # sensible heat removed from the system with the H2 and O2 streams, as well
        # as the sensible heat required to warm the deionized water from room temperature
        # to the stack operating temperature
        sensible_heat = (
                                mass_H2O * self.c_p_H2O * (self.temp_min - new_ely_temp)
                                - mass_H2 * self.c_p_H2 * (new_ely_temp - self.temp_min)
                                - mass_O2 * self.c_p_O2 * (new_ely_temp - self.temp_min)
                        ) / 3.6e6  # [kWh], 1J = 1/3.6e6 kWh
        # latent heat is neglected since mass_H2O_vapor is neglected
        latent_heat = 0
        return [sensible_heat, latent_heat]

    def update_constraints(self, busses, model_to_solve):
        """Set a constraint so that the electric inflow of the hydrogen producing and the
        thermal part are always the same (which is necessary while the piecewise linear
        transformer cannot have two outputs yet and therefore the two parts need to be
        separate components).

        :param busses: The virtual buses used in the energy system
        :type busses: list
        :param model_to_solve: The oemof model that will be solved
        :type model_to_solve: model
        """

        def electrolyzer_ratio_rule(model, t):
            """Ensures that the flows going into the electrolyzer hydrogen production
            component and those going into the electrolyser thermal energy production
            component are equal.

            :param model: The oemof model containing the hydrogen production and thermal
                energy production of the electrolyser
            :type model: model
            :param t: ?
            :return: expression = 0
            """
            expr = 0
            expr += model.flow[busses[self.bus_el], self.model_th, t]
            expr += -model.flow[busses[self.bus_el], self.model_h2, t]
            return expr == 0

        model_to_solve.electrolyzer_flow_ratio_fix = po.Constraint(
            model_to_solve.TIMESTEPS, rule=electrolyzer_ratio_rule
        )

    def update_flows(self, results, sim_params):
        """Updates the flows of the electrolyser waste heat components for each time
        step.

        :param results: The oemof results for the given time step
        :type results: object
        :param sim_params: The simulation parameters for the energy system (defined by user)
        :type sim_params: object
        :return: updated flow values for each flow in the 'flows' dict
        """
        # Check if the component has an attribute 'flows', if not, create it as an empty dict.
        Electrolyzer.update_flows(self, results, sim_params, self.name)
        Electrolyzer.update_flows(
            self, results, sim_params, self.name + "_thermal"
        )
