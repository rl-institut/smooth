"""
This module represents a combined heat and power (CHP) system with a fuel cell,
using hydrogen to generate electricity and heat.

*****
Scope
*****
The importance of a fuel cell CHP component in dynamic energy systems is its
potential to enable better sector coupling between the electricity and
heating sectors, thus less dependence on centralised power systems by
offering the ability for localised energy supply [1].

*******
Concept
*******
The fuel cell CHP has a hydrogen bus input along with an electrical bus and
thermal bus output. The behaviour of the fuel cell CHP component is non-linear,
which is demonstrated through the use of oemof's Piecewise Linear Transformer
component.

Efficiency
----------
The efficiency curves for both electrical and thermal energy output according
to nominal load which are considered for the fuel cell CHP component are
displayed in INSERT FIGURE. From the breakpoints, the electrical and thermal
production based on the hydrogen consumption and variable efficiency can be
obtained.

INCLUDE EFFICIENCY CURVE FIGURE

Electrical and thermal energy production
----------------------------------------
In order to calculate the electrical and thermal energy production for
each load point, first the maximum hydrogen input is calculated:

.. math::
    H_{2,max} = \\frac{P_{max}}{LHV_{H_2}} \\cdot \\mu_{elec_{full load}}

* :math:`H_{2,max}` = maximum hydrogen input per timestep [kg]
* :math:`P_{max}` = maximum electrical output power [W]
* :math:`\mu_{elec_{max}}` = electrical efficiency at full load [-]

Then the load break points for both the electrical and thermal components
 are converted into how much hydrogen is consumed at each load break point
according to the maximum hydrogen input per time step:

.. math::
    bp_{H_{2},el,i} = bp_{load,el,i} \\cdot H_{2,max} \n
    bp_{H_{2},th,i} = bp_{load,th,i} \\cdot H_{2,max}

* :math:`bp_{H_{2},el,i}` = ith electrical break point in terms of hydrogen consumption [kg]
* :math:`bp_{load,el,i}` = ith electrical break point in terms of nominal load [-]
* :math:`bp_{H_{2},th,i}` = ith thermal break point in terms of hydrogen consumption [kg]
* :math:`bp_{load,th,i}` = ith thermal break point in terms of nominal load [-]

From these hydrogen consumption values, the absolute electrical and thermal
energy produced at each break point is calculated:

.. math::
    E_{el,i} = bp_{H_{2},el,i} \\cdot \\mu_{el,i} \\cdot LHV_{H_{2}} \\cdot 1000 \n
    E_{th,i} = bp_{H_{2},th,i} \\cdot \\mu_{th,i} \\cdot LHV_{H_{2}} \\cdot 1000

* :math:`E_{el,i}` = ith absolute electrical energy value [Wh]
* :math:`\\mu_{el,i}` = ith electrical efficiency [-]
* :math:`E_{th,i}` = ith absolute thermal energy value [Wh]
* :math:`\\mu_{th,i}` = ith thermal efficiency [-]

Piecewise Linear Transformer
----------------------------
Currently, the piecewise linear transformer component in oemof can only
represent a one-to-one transformation with a singular input and a singular
output. Thus, in order to represent the non-linear fuel cell CHP in the
energy system, two oemof components are created for the electrical and
thermal outputs individually, with a constraint that the hydrogen input flows
into each component must always be equal. In this way, the individual oemof
components behave as one component.

References
----------
[1] P.E. Dodds et.al. (2015). Hydrogen and fuel cell technologies for heat: A
review, International journal of hydrogen energy.
"""

from smooth.components.component import Component
import oemof.solph as solph
import pyomo.environ as po


class FuelCellChp(Component):
    """
    :param name: unique name given to the fuel cell CHP component
    :type name: str
    :param bus_h2: hydrogen bus that is the input of the CHP
    :type bus_h2: str
    :param bus_el: electricity bus that is the output of the CHP
    :type bus_el: str
    :param bus_th: thermal bus that is the output of the CHP
    :type bus_th: str
    :param power_max: maximum electrical output power [W]
    :type power_max: numerical
    :param set_parameters(params): updates parameter default values (see generic Component class)
    :type set_parameters(params): function
    :param heating_value_h2: heating value of hydrogen [kWh/kg]
    :type heating_value_h2: numerical
    :param bp_load_el: electrical efficiency load break points [-]
    :type bp_load_el: list
    :param bp_eff_el: electrical efficiency break points [-]
    :type bp_eff_el: list
    :param bp_load_th: thermal efficiency load break points [-]
    :type bp_load_th: list
    :param bp_eff_th: thermal efficiency break points [-]
    :type bp_eff_th: list
    :param h2_input_max: maximum hydrogen input that leads to maximum electrical energy in Wh [kg]
    :type h2_input_max: numerical
    :param bp_h2_consumed_el: converted electric load points according to maximum hydrogen
        input per time step [kg]
    :type bp_h2_consumed_el: list
    :param bp_h2_consumed_th: converted thermal load points according to maximum hydrogen
        input per time step [kg]
    :type bp_h2_consumed_th: list
    :param bp_energy_el: absolute electrical energy values over the load points [Wh]
    :type bp_energy_el: list
    :param bp_energy_th: absolute thermal energy values over the load points [Wh]
    :type bp_energy_th: list
    :param bp_h2_consumed_el_half: half the amount of hydrogen that is consumed [kg]
    :type bp_h2_consumed_el_half: list
    :param bp_h2_consumed_th_half: half the amount of hydrogen that is consumed [kg]
    :type bp_h2_consumed_th_half: list
    :param model_el: electric model to set constraints later
    :type model_el: model
    :param model_th: thermal model to set constraints later
    :type model_th: model
    """

    def __init__(self, params):
        """Constructor method
        """
        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        # PARAMETERS TO CHANGE BY THE USER
        self.name = 'Fuel cell CHP default name'
        # Busses (H2 in, electrical out, thermal out).
        self.bus_h2 = None
        self.bus_el = None
        self.bus_th = None
        # Max. electrical output power [W].
        self.power_max = None
        # Lifetime of the component [a]
        self.life_time = 15
        # Update the input parameters by the user.
        self.set_parameters(params)
        # INTERNAL PARAMETERS
        # Heating value of hydrogen [kWh/kg].
        self.heating_value_h2 = 33.33
        # The CHP an electrical efficiency and a thermal efficiency, both over
        # the load point, according to: Scholta, J. et.al. Small Scale PEM Fuel
        # Cells in Combined Heat/Power Co-generation. RCUB Afrodita.
        # http://afrodita.rcub.bg.ac.rs/~todorom/tutorials/rad24.html
        # Electrical efficiency load break points (e.g. 0.05 --> 5 %) [-]
        self.bp_load_el = [0.0, 0.0481, 0.0694, 0.0931, 0.1272, 0.1616, 0.2444, 0.5912, 1.0]
        # Electrical efficiency break points (e.g. 0.05 --> 5 %) [-]
        self.bp_eff_el = [0.0, 0.1996, 0.3028, 0.4272, 0.5034, 0.5381, 0.5438, 0.4875, 0.3695]
        # Thermal efficiency load break points (e.g. 0.05 --> 5 %) [-].
        self.bp_load_th = [0.0, 0.0517, 0.1589, 0.2482, 1.0]
        # Thermal efficiency break points (e.g. 0.05 --> 5 %) [-].
        self.bp_eff_th = [0.0, 0.0915, 0.2188, 0.2795, 0.5238]
        # Now calculate the absolute values for electricity [Wh] and thermal
        # energy [Wh] and H2 consumption [kg].
        # Therefor first calculate the max. hydrogen input that lead to the
        # max. electrical energy in Wh [kg].
        self.h2_input_max = self.power_max / (
            self.heating_value_h2 * self.bp_eff_el[-1]) * \
            self.sim_params.interval_time / 60 / 1000
        # Now convert the load points according to the max. hydrogen input per time step [kg].
        self.bp_h2_consumed_el = [
            this_bp * self.h2_input_max for this_bp in self.bp_load_el]
        self.bp_h2_consumed_th = [
            this_bp * self.h2_input_max for this_bp in self.bp_load_th]
        # Now get the absolute electrical energy values over the load points [Wh].
        self.bp_energy_el = []
        for i_bp in range(len(self.bp_load_el)):
            # Calculate the electrical energy produced at this breaking point [Wh]
            this_energy_el = \
                self.bp_h2_consumed_el[i_bp] * \
                self.bp_eff_el[i_bp] * self.heating_value_h2 * 1000
            self.bp_energy_el.append(this_energy_el)
        # Now get the absolute thermal energy values over the load points [Wh].
        self.bp_energy_th = []
        for i_bp in range(len(self.bp_load_th)):
            # Calculate the thermal energy produced at this breaking point [Wh]
            this_energy_th = \
                self.bp_h2_consumed_th[i_bp] * \
                self.bp_eff_th[i_bp] * self.heating_value_h2 * 1000
            self.bp_energy_th.append(this_energy_th)
        # While we will create two oemof components, one for thermal energy and
        # one for electrical energy, and make a constraint that both inflows of
        # hydrogen have to be the same, each component will get only half the
        # amount of hydrogen. Therefore we need to make a list of hydrogen
        # consumed that is halfed [kg]
        self.bp_h2_consumed_el_half = [
            this_bp / 2 for this_bp in self.bp_h2_consumed_el]
        self.bp_h2_consumed_th_half = [this_bp / 2 for this_bp in self.bp_h2_consumed_th]
        # Save the two models to set constraints later.
        self.model_el = None
        self.model_th = None

    def get_el_energy_by_h2(self, h2_consumption):
        """Gets the electrical energy produced by the according hydrogen consumption value.

        :param h2_consumption: hydrogen consumption value [kg]
        :return: according electrical energy value [Wh]
        """
        # Check the index of this load point.
        this_index = self.bp_h2_consumed_el_half.index(h2_consumption)
        return self.bp_energy_el[this_index]

    def get_th_energy_by_h2(self, h2_consumption):
        """Gets the thermal energy produced by the according hydrogen consumption value.

        :param h2_consumption: hydrogen consumption value [kg]
        :return: according thermal energy value [Wh]
        """
        # Check the index of this load point.
        this_index = self.bp_h2_consumed_th_half.index(h2_consumption)
        return self.bp_energy_th[this_index]

    def create_oemof_model(self, busses, model):
        """Creates two separate oemof Piecewise Linear Transformer components for the
        electrical and thermal production of the fuel cell CHP from information given
        in the FuelCellCHP class, to be used in the oemof model

        :param busses: virtual buses used in the energy system
        :type busses: list
        :param model: oemof model containing the electrical energy production and
            thermal energy production of the fuel cell CHP
        :type model: model
        :return: the oemof fuel cell CHP electric and thermal components
        """
        # The CHP has to be modelled as two components, while the piecewise linear
        # transformer does not accept 2 outputs yet.

        flow_electric = solph.Flow(
            nominal_value=self.bp_h2_consumed_el_half[-1],
            variable_costs=0)
        flow_thermal = solph.Flow(nominal_value=self.bp_h2_consumed_el_half[-1])

        # First create the electrical oemof component.
        fuel_cell_chp_electric = solph.custom.PiecewiseLinearTransformer(
            label=self.name+'_electric',
            inputs={busses[self.bus_h2]: flow_electric},
            outputs={busses[self.bus_el]: solph.Flow()},
            in_breakpoints=self.bp_h2_consumed_el_half,
            conversion_function=self.get_el_energy_by_h2,
            pw_repn='CC')

        # Then create the thermal oemof component.
        fuel_cell_chp_thermal = solph.custom.PiecewiseLinearTransformer(
            label=self.name+'_thermal',
            inputs={busses[self.bus_h2]: flow_thermal},
            outputs={busses[self.bus_th]: solph.Flow()},
            in_breakpoints=self.bp_h2_consumed_th_half,
            conversion_function=self.get_th_energy_by_h2,
            pw_repn='CC')

        # Add the two components to the model.
        model.add(fuel_cell_chp_electric, fuel_cell_chp_thermal)

        self.model_el = fuel_cell_chp_electric
        self.model_th = fuel_cell_chp_thermal

        return None

    def update_constraints(self, busses, model_to_solve):
        """Set a constraint so that the hydrogen inflow of the electrical and
        the thermal part are always the same (which is necessary while the
        piecewise linear transformer cannot have two outputs yet and
        therefore the two parts need to be separate components).

        :param busses: virtual buses used in the energy system
        :type busses: list
        :param model_to_solve: The oemof model that will be solved
        :type model_to_solve: model
        """

        def chp_ratio_rule(model, t):
            """Ensures that the flows going into the fuel cell CHP electricity production
            component and those going into the fuel cell CHP thermal energy production
            component are equal.

            :param model: The oemof model containing the electrical energy production and
                thermal energy production of the fuel cell
            :type model: model
            :param t: ?
            :return: expression = 0
            """
            # Inverter flow
            expr = 0
            expr += model.flow[busses[self.bus_h2], self.model_th, t]
            expr += - model.flow[busses[self.bus_h2], self.model_el, t]
            return (expr == 0)

        setattr(model_to_solve,
                'chp_flow_ratio_fix_{}'.format(self.name.replace(' ', '')),
                po.Constraint(model_to_solve.TIMESTEPS, rule=chp_ratio_rule)
                )

    def update_flows(self, results, sim_params):
        """Updates the flows of the fuel cell CHP components for each time step.

        :param results: The oemof results for the given time step
        :type results: object
        :param sim_params: The simulation parameters for the energy system (defined by user)
        :type sim_params: object
        :return: updated flow values for each flow in the 'flows' dict
        """
        # Check if the component has an attribute 'flows', if not, create it as an empty dict.
        Component.update_flows(self, results, sim_params, self.name + '_electric')
        Component.update_flows(self, results, sim_params, self.name + '_thermal')
