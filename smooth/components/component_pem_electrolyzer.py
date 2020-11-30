"""
Polymer electrolyte membrane (PEM) electrolyzer agents are
created through this class.

*****
Scope
*****
Despite being less mature in the development phase than alkaline electrolysis,
thus having higher manufacturing costs, PEM electrolysis has advantages such
as quick start-up times, simple maintenance and composition, as well as no
dangers of corrosion [1]. If the manufacturing costs of PEM electrolyzers can
be reduced by economy of scale, these electrolyzers have the potential to
be crucial components in a self-sufficient renewable energy system.

*******
Concept
*******
The PEM electrolyzer is modelled using oemof's Piecewise Linear Transformer
components, and the component as a whole represents the intake of
electricity to produce hydrogen and waste heat as a by-product.

.. figure:: /images/pem_electrolyzer.png
    :width: 60 %
    :alt: pem_electrolyzer.png
    :align: center

    Fig.1: Simple diagram of a PEM electrolyzer.

Efficiency
----------
The amount of hydrogen and waste heat production is dependant on variable
efficiencies according to nominal load, as displayed in INSERT FIGURE.

INCLUDE EFFICIENCY CURVE FIGURE

Hydrogen and waste heat production
----------------------------------
The maximum power of the electrolyzer, as defined by the user, is used
to determine how much electricity is consumed at each load break point.

.. math::
    bp_{el,H_{2},i} = bp_{load,H_{2},i} \\cdot P_{max} \n
    bp_{el,th,i} = bp_{load,th,i} \\cdot P_{max}

* :math:`bp_{el,H_{2},i}` = ith hydrogen break point in terms of electricity consumption [Wh]
* :math:`bp_{load,H_{2},i}` = ith hydrogen break point in terms of nominal load [-]
* :math:`bp_{el,th,i}` = ith thermal break point in terms of electricity consumption [Wh]
* :math:`bp_{load,th,i}` = ith thermal break point in terms of nominal load [-]

From these electricity consumption values, the absolute hydrogen and waste heat
energy produced at each break point is calculated:

.. math::
    H_{2_{prod,i}} = \\frac{bp_{el,H_{2},i} \\cdot \\mu_{H_{2},i}}{LHV_{H_{2}} \\cdot 1000} \n
    E_{th,i} = bp_{el,th,i} \\cdot \\mu_{th,i}

* :math:`H_{2_{prod,i}}` = ith absolute hydrogen production value [kg]
* :math:`\\mu_{H_{2},i}}` = ith hydrogen production efficiency [-]
* :math:`E_{th,i}` = ith absolute thermal energy value [Wh]
* :math:`\\mu_{th,i}` = ith thermal efficiency [-]

Piecewise Linear Transformer
----------------------------
The PEM electrolyzer component uses oemof's Piecewise Linear Tansformer
component in a similar fashion to the fuel cell CHP and the biogas CHP.
For more detail on the usage, visit the Fuel Cell CHP or Gas Engine
CHP Biogas components.

References
----------
[1] Guo, Y. et.al. (2019). Comparison between hydrogen production by alkaline
water electrolysis and hydrogen production by PEM electrolysis. IOP Conference
Series: Earth and Environmental Science.
"""

import oemof.solph as solph
from .component import Component
import pyomo.environ as po


class PemElectrolyzer(Component):
    """
    :param name: unique name given to PEM electrolyzer component
    :type name: str
    :param bus_el: electricity bus input of the PEM electrolyzer
    :type bus_el: str
    :param bus_h2: hydrogen bus output of the PEM electrolyzer
    :type bus_h2: str
    :param bus_th: thermal bus output of the PEM electrolyzer
    :type bus_th: str
    :param power_max: maximum electrical input power [W]
    :type power_max: numerical
    :param life_time: life time of the component [a]
    :type life_time: str
    :param set_parameters(params): updates parameter default values
        (see generic Component class)
    :type set_parameters(params): function
    :param heating_value: heating value of hydrogen [kWh/kg]
    :type heating_value: numerical
    :param bp_load_h2_prod: hydrogen production efficiency load break points [-]
    :type bp_load_h2_prod: list
    :param bp_eff_h2_prod: hydrogen production efficiency break points [-]
    :type bp_eff_h2_prod: list
    :param bp_load_waste_heat: waste heat efficiency load break points [-]
    :type bp_load_waste_heat: list
    :param bp_eff_waste_heat: waste heat efficiency break points [-]
    :type bp_eff_waste_heat: list
    :param bp_elec_consumed_h2_prod: converted hydrogen production load points
        according to maximum power per timestep [Wh]
    :type bp_elec_consumed_h2_prod: list
    :param bp_elec_consumed_waste_heat: converted waste heat load points
        according to maximum power per timestep [Wh]
    :type bp_elec_consumed_waste_heat: list
    :param bp_h2_production: absolute hydrogen production values over the load points [kg]
    :type bp_h2_production: list
    :param bp_waste_heat_energy: absolute waste heat energy values over the load points [Wh]
    :type bp_h2_production: list
    :param bp_elec_consumed_h2_prod_half: half the amount of electricity that is
        consumed [Wh]
    :type bp_elec_consumed_h2_prod_half: list
    :param bp_elec_consumed_waste_heat_half: half the amount of electricity that is
        consumed [Wh]
    :type bp_elec_consumed_h2_prod_half: list
    :param model_h2: hydrogen production model to set constraints later
    :type model_h2: model
    :param model_th: waste heat model to set constraints later
    :type model_th: model
    """

    def __init__(self, params):
        """Constructor method
        """
        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = 'PEM_electrolyzer_default_name'
        self.bus_el = None
        self.bus_h2 = None
        self.bus_th = None
        # Max. electrical input power [W].
        self.power_max = 6000000
        # Life time [a].
        self.life_time = 10

        # ToDo: check if pressure/temperature of electrolyzer should be included

        # Update the input parameters by the user.
        self.set_parameters(params)

        # INTERNAL PARAMETERS
        # Heating value of hydrogen [kWh/kg].
        self.heating_value = 33.33

        # The efficiency curve for the system efficiency over the load point of a PEM
        # electrolyzer, according to:
        # Waidhas, M. 'Electrolyzer technology - the Siemens view' 2016.
        # http://www.scandinavianhydrogen.org/wp-content/uploads/2016/11/2_Manfred-Waidhas.pdf

        self.bp_load_h2_prod = [0.0255, 0.0398, 0.0582, 0.0797, 0.0991, 0.1267, 0.1624, 0.2257,
                                0.3565, 0.4545, 0.5832, 0.6803, 0.8151, 0.9418, 1.0]

        self.bp_eff_h2_prod = [0, 0.2157, 0.4762, 0.563, 0.6303, 0.6751, 0.6947, 0.6863, 0.6779,
                               0.6583, 0.6387, 0.6218, 0.6022, 0.5854, 0.5798]

        # The (approximated) efficiency curve for the waste heat efficiency
        # over the load point of a PEM electrolyzer,
        # according to: Ni, M. et.al. 'Energy and exergy
        # analysis of hydrogen production by a proton exchange membrane
        # (PEM) electrolyzer plant' 2008 and Waidhas,
        # M. 'Electrolyzer technology - the Siemens view' 2016.

        # Waste heat efficiency load break points (e.g. 0.05 --> 5 %) [-]
        self.bp_load_waste_heat = [0.02859, 0.1659, 0.3413, 0.5082, 0.6721, 0.8317, 1.0]
        # Waste heat efficiency break points (e.g. 0.05 --> 5 %) [-]
        self.bp_eff_waste_heat = [0, 0.0519, 0.1205, 0.1826, 0.2529, 0.3235, 0.4140]

        # Convert the load points according to the maximum power per timestep [?]
        self.bp_elec_consumed_h2_prod = [this_bp * self.power_max
                                         for this_bp in self.bp_load_h2_prod]
        self.bp_elec_consumed_waste_heat = [this_bp * self.power_max
                                            for this_bp in self.bp_load_waste_heat]

        # Now get the absolute hydrogen production values over the load points [kg]
        self.bp_h2_production = []
        for i_bp in range(len(self.bp_load_h2_prod)):
            this_hydrogen_production = \
                (self.bp_elec_consumed_h2_prod[i_bp]
                 * self.bp_eff_h2_prod[i_bp]) / (self.heating_value * 1000)
            self.bp_h2_production.append(this_hydrogen_production)

        # Now get the absolute waste heat energy values over the load points [Wh]
        self.bp_waste_heat_energy = []
        for i_bp in range(len(self.bp_load_waste_heat)):
            # Calculate the waste heat energy produced at this break point [Wh]
            this_waste_heat_energy = self.bp_elec_consumed_waste_heat[i_bp] \
                * self.bp_eff_waste_heat[i_bp]
            self.bp_waste_heat_energy.append(this_waste_heat_energy)

        # While we will create two oemof components, one for the e
        # lectrolyzer producing hydrogen and one for the
        # electrolyzer producing waste heat energy,
        # and make a constraint that both inflows of electricity have to be
        # the same, each component will get only half the amount of electricity.
        # Therefore we need to make a list of
        # electricity consumed that is halfed [Wh]
        self.bp_elec_consumed_h2_prod_half = [this_bp / 2
                                              for this_bp in self.bp_elec_consumed_h2_prod]
        self.bp_elec_consumed_waste_heat_half = [this_bp / 2
                                                 for this_bp in self.bp_elec_consumed_waste_heat]

        # Save the two models to set constraints later
        # (h2 for hydrogen production and th for waste heat energy).
        self.model_h2 = None
        self.model_th = None

    def get_h2_production_by_electricity(self, electricity_consumption):
        """Gets the hydrogen produced by the according electricity consumption
        value.

        :param electricity_consumption: electrcity consumption value [Wh]
        :return: according hydrogen production value [kg]
        """
        # Check the index of this load point.
        this_index = self.bp_elec_consumed_h2_prod_half.index(electricity_consumption)
        return self.bp_h2_production[this_index]

    def get_waste_heat_energy_by_electricity(self, electricity_consumption):
        """Gets the waste heat produced by the according electricity consumption
        value.

        :param electricity_consumption: electrcity consumption value [Wh]
        :return: according waste heat value [Wh]
        """
        # Check the index of this load point.
        this_index = self.bp_elec_consumed_waste_heat_half.index(electricity_consumption)
        # Return the according waste heat energy value [Wh]
        return self.bp_waste_heat_energy[this_index]

    def create_oemof_model(self, busses, model):
        """Creates two separate oemof Piecewise Linear Transformer components for the
        hydrogen and waste heat production of the PEM electrolyzer from information
        given in the PEMElectrolyzer class, to be used in the oemof model

        :param busses: virtual buses used in the energy system
        :type busses: list
        :param model: oemof model containing the hydrogen production and
            waste heat production of the PEM electrolyzer
        :type model: model
        :return: the oemof PEM electrolyzer hydrogen and waste heat components
        """
        # The PEM electrolyzer has to be modelled as two components, while the
        # piecewise linear transformer does not accept 2 outputs yet.

        flow_h2 = solph.Flow(
            nominal_value=self.bp_elec_consumed_h2_prod_half[-1],
            variable_costs=0)
        flow_waste_heat = solph.Flow(nominal_value=self.bp_elec_consumed_waste_heat_half[-1])

        # First create the main PEM electrolyzer oemof component.
        pem_electrolyzer_h2_prod = solph.custom.PiecewiseLinearTransformer(
            label=self.name + '_h2_prod',
            inputs={busses[self.bus_el]: flow_h2},
            outputs={busses[self.bus_h2]: solph.Flow()},
            in_breakpoints=self.bp_elec_consumed_h2_prod_half,
            conversion_function=self.get_h2_production_by_electricity,
            pw_repn='CC')

        # Then create the waste heat PEM electrolyzer oemof component.
        pem_electrolyzer_waste_heat = solph.custom.PiecewiseLinearTransformer(
            label=self.name + '_waste_heat',
            inputs={busses[self.bus_el]: flow_waste_heat},
            outputs={busses[self.bus_th]: solph.Flow()},
            in_breakpoints=self.bp_elec_consumed_waste_heat_half,
            conversion_function=self.get_waste_heat_energy_by_electricity,
            pw_repn='CC')

        # Add the two components to the model
        model.add(pem_electrolyzer_h2_prod, pem_electrolyzer_waste_heat)

        self.model_h2 = pem_electrolyzer_h2_prod
        self.model_th = pem_electrolyzer_waste_heat

        return None

    def update_constraints(self, busses, model_to_solve):
        """Set a constraint so that the electricity inflow of the hydrogen and
        the waste heat part are always the same (which is necessary while the
        piecewise linear transformer cannot have two outputs yet and
        therefore the two parts need to be separate components).

        :param busses:
        :param model_to_solve:
        :return:
        """

        def electrolyzer_ratio_rule(model, t):
            """Ensures that the flows going into the PEM electrolyzer hydrogen production
            component and those going into the PEM electrolyzer waste heat production
            component are equal.

            :param model: The oemof model containing the hydrogen production and waste
                heat production of the electrolyzer
            :type model: model
            :param t: ?
            :return: expression = 0
            """
            # Inverter flow
            expr = 0
            expr += model.flow[busses[self.bus_el], self.model_th, t]
            expr += - model.flow[busses[self.bus_el], self.model_h2, t]
            return (expr == 0)

        setattr(model_to_solve,
                'electrolyzer_flow_ratio_fix_{}'.format(self.name.replace(' ', '')),
                po.Constraint(model_to_solve.TIMESTEPS, rule=electrolyzer_ratio_rule)
                )

    def update_flows(self, results, sim_params):
        """Updates the flows of the electrolyzer components for each time step.

        ::param results: The oemof results for the given time step
        :type results: object
        :param sim_params: The simulation parameters for the energy system (defined by user)
        :type sim_params: object
        :return: updated flow values for each flow in the 'flows' dict
        """
        # Check if the component has an attribute 'flows', if not, create it as an empty dict.
        Component.update_flows(self, results, sim_params, self.name + '_h2_prod')
        Component.update_flows(self, results, sim_params, self.name + '_waste_heat')
