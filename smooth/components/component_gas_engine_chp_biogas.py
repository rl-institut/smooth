"""
A combined heat and power (CHP) plant with a gas engine, using biogas to
generate electricity and heat is created through this class.

*****
Scope
*****
Biogas CHPs play a significant role in renewable energy systems by using
biogas, which has been produced from organic waste material, as a fuel source
to produce both electricity and heat. The utilisation of biogas CHPs is
beneficial for sector coupling and the minimisation of methane emissions as
a result of using up the biogas.

*******
Concept
*******
The biogas CHP component requires a biogas bus input in order to output an
electrical and a thermal bus, and oemof's Piecewise Linear Transformer
component is chosen to represent the nonlinear efficiencies of the biogas
CHP. The method used in this component is similar to the fuel cell CHP
component.

.. figure:: /images/gas_engine_chp_biogas.png
    :width: 60 %
    :alt: gas_engine_chp_biogas.png
    :align: center

    Fig.1: Simple diagram of a biogas gas engine CHP.

Biogas composition
------------------
The user can determine the desired composition of biogas by stating the
percentage share of methane and carbon dioxide in the gas (the default
is 50-50 % share). The lower heating value (LHV) of methane is 13.9
kWh/kg [1], and the molar masses of methane and carbon dioxide are
0.01604 kg/mol and 0.04401 kg/mol, respectively. The gas composition is
given as a mole percentage, and this percentage is transformed into a
mass percentage. Finally, the heating value of the biogas is found by
multiplying the mass percentage with the LHV of methane, which is
demonstrated below:

.. math::
    LHV_{Bg} = \\frac{CH_{4_{share}} \\cdot M_{CH_{4}}}{CH_{4_{share}} \\cdot
    M_{CH_{4}} + CO_{2_{share}} \\cdot M_{CO_{2}}} \\cdot LHV_{CH_{4}} \n

* :math:`LHV_{Bg}` = heating value of biogas [kWh/kg]
* :math:`CH_{4_{share}` = proportion of methane in biogas [-]
* :math:`M_{CH_{4}}` = molar mass of methane [kg/mol]
* :math:`CO_{2_{share}}` = proportion of carbon dioxide in biogas [-]
* :math:`M_{CO_{2}}` = molar mass of carbon dioxide [kg/mol]
* :math:`LHV_{CH_{4}}` = heating value of methane [kWh/kg]

Efficiency
----------
The electrical and thermal production from the CHP is determined by variable
efficiencies according to nominal load, and the efficiency curves used in the
component can be seen in Figure 2. The piecewise linear representation that
is actually used in the SMOOTH component is shown in the left image, and the
approximated efficiency curve is shown in the right image.

.. figure:: /images/chp_biogas_efficiency.png
    :width: 100 %
    :alt: chp_biogas_efficiency.png
    :align: center

    Fig.2: Piecewise and approximated efficiency of biogas gas engine CHP.

Electrical and thermal energy production
----------------------------------------
The maximum biogas input is initially calculated so that the electrical
and thermal energy production for each load point can be calculated:

.. math::
    Bg_{max} = \\frac{P_{max}}{LHV_{Bg}} \\cdot \\mu_{elec_{full load}}

* :math:`Bg_{max}` = maximum biogas input per timestep [kg]
* :math:`P_{max}` = maximum electrical output power [W]
* :math:`\\mu_{elec_{max}}` = electrical efficiency at full load [-]

Then the load break points for both the electrical and thermal components
 are converted into how much biogas is consumed at each load break point
according to the maximum biogas input per time step:

.. math::
    bp_{Bg,el,i} = bp_{load,el,i} \\cdot Bg_{max} \n
    bp_{Bg,th,i} = bp_{load,th,i} \\cdot Bg_{max}

* :math:`bp_{Bg,el,i}` = ith electrical break point in terms of biogas consumption [kg]
* :math:`bp_{load,el,i}` = ith electrical break point in terms of nominal load [-]
* :math:`bp_{Bg,th,i}` = ith thermal break point in terms of biogas consumption [kg]
* :math:`bp_{load,th,i}` = ith thermal break point in terms of nominal load [-]

From these biogas consumption values, the absolute electrical and thermal
energy produced at each break point is calculated:

.. math::
    E_{el,i} = bp_{Bg,el,i} \\cdot \\mu_{el,i} \\cdot LHV_{Bg} \\cdot 1000 \n
    E_{th,i} = bp_{Bg,th,i} \\cdot \\mu_{th,i} \\cdot LHV_{Bg} \\cdot 1000

* :math:`E_{el,i}` = ith absolute electrical energy value [Wh]
* :math:`\\mu_{el,i}` = ith electrical efficiency [-]
* :math:`E_{th,i}` = ith absolute thermal energy value [Wh]
* :math:`\\mu_{th,i}` = ith electrical efficiency [-]

Piecewise Linear Transformer
----------------------------
As stated in the fuel cell CHP component, two seperate oemof components
for the electrical and thermal production of the biogas CHP must be created,
but they still behave as one component by setting a constraint that the
biogas input flows into the two components are always equal.

References
----------
[1] Linde Gas GmbH (2013). Rechnen Sie mit Wasserstoff. Die Datentabelle.
"""


from smooth.components.component import Component
import oemof.solph as solph
import pyomo.environ as po


class GasEngineChpBiogas(Component):
    """
    :param name: unique name given to the biogas gas engine CHP component
    :type name: str
    :param bus_bg: biogas bus input of the CHP
    :type bus_bg: str
    :param bus_el: electrical bus input of the CHP
    :type bus_el: str
    :param bus_th: thermal bus input of the CHP
    :type bus_th: str
    :param power_max: maximum electrical output power [W]
    :type power_max: numerical
    :param ch4_share: proportion of methane in biogas [-]
    :type ch4_share: numerical
    :param co2_share: proportion of carbon dioxide in biogas [-]
    :type co2_share: numerical
    :param set_parameters(params): updates parameter default values (see generic Component class)
    :type set_parameters(params): function
    :param heating_value_ch4: heating value of methane [kWh/kg]
    :type heating_value_ch4: numerical
    :param mol_mass_ch4: molar mass of methane [kg/mol]
    :type mol_mass_ch4: numerical
    :param mol_mass_co2: molar mass of carbon dioxide [kg/mol]
    :type mol_mass_co2: numerical
    :param heating_value_bg: heating value of biogas [kWh/kg]
    :type heating_value_bg: numerical
    :param bp_load_el: electrical efficiency load break points [-]
    :type bp_load_el: list
    :param bp_eff_el: electrical efficiency break points [-]
    :type bp_eff_el: list
    :param bp_load_th: thermal efficiency load break points [-]
    :type bp_load_th: list
    :param bp_eff_th: thermal efficiency break points [-]
    :type bp_eff_th: list
    :param bg_input_max: maximum biogas input that leads to the
        maximum electrical energy in Wh [kg]
    :type bg_input_max: numerical
    :param bp_bg_consumed_el: converted electric load points according
        to maximum hydrogen input per time step [kg]
    :type bp_bg_consumed_el: list
    :param bp_bg_consumed_th: converted thermal load points according to
        maximum hydrogen input per time step [kg]
    :type bp_bg_consumed_th: list
       :param bp_energy_el: absolute electrical energy values over the load points [Wh]
    :type bp_energy_el: list
    :param bp_energy_th: absolute thermal energy values over the load points [Wh]
    :type bp_energy_th: list
    :param bp_bg_consumed_el_half: half the amount of biogas that is consumed [kg]
    :type bp_bg_consumed_el_half: list
    :param bp_bg_consumed_th_half: half the amount of biogas that is consumed [kg]
    :type bp_bg_consumed_th_half: list
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
        self.name = 'Gas Engine CHP Biogas default name'

        # Busses (biogas in, electrical out, thermal out).
        self.bus_bg = None
        self.bus_el = None
        self.bus_th = None

        # Max. electrical output power [W].
        self.power_max = None

        # gas composition
        self.ch4_share = 0.5
        self.co2_share = 0.5

        # Update the input parameters by the user.
        self.set_parameters(params)

        if self.ch4_share + self.co2_share != 1:
            raise ValueError("addition of all shares must be 1")

        # INTERNAL PARAMETERS
        # Heating value of methane [kWh/kg].
        # [kWh/kg]
        # https://www.linde-gas.at/de/images/1007_rechnen_sie_mit_wasserstoff_v110_tcm550-169419.pdf
        self.heating_value_ch4 = 13.9

        # mol masses ch4 and co2
        self.mol_mass_ch4 = 0.01604  # [kg/mol]
        self.mol_mass_co2 = 0.04401  # [kg/mol]

        # Heating value of biogas [kWh/kg].
        # The gas composition is given as a mol percentage. In the following
        # this percentage will be transformed into a mass percentage and
        # finally into the heating value of the biogas by multiplying it with
        # the LHV of CH4
        self.heating_value_bg = ((self.ch4_share * self.mol_mass_ch4) /
                                 ((self.ch4_share * self.mol_mass_ch4) +
                                  (self.co2_share * self.mol_mass_co2))) * self.heating_value_ch4

        # The CHP an electrical efficiency and a thermal efficiency
        # Source: 2G Energy AG Technical specification agenitor 206 BG,
        #   http://www.n2ies.com/pdf/2g-agenitor.pdf
        # Electrical efficiency load break points (e.g. 0.05 --> 5 %) [-]
        self.bp_load_el = [0, 0.5, 0.75, 1.0]
        # Electrical efficiency break points (e.g. 0.05 --> 5 %) [-]
        self.bp_eff_el = [0, 0.349, 0.370, 0.387]

        # Thermal efficiency load break points (e.g. 0.05 --> 5 %) [-].
        self.bp_load_th = [0, 0.5, 0.75, 1.0]
        # Thermal efficiency break points (e.g. 0.05 --> 5 %) [-].
        self.bp_eff_th = [0, 0.459, 0.438, 0.427]

        # Now calculate the absolute values for electricity [Wh] and thermal
        # energy [Wh] and ch4 consumption [kg].

        # Therefore first calculate the max. biomethane input that lead to the
        # max. electrical energy in Wh [kg].
        self.bg_input_max = self.power_max / \
            (self.heating_value_bg * self.bp_eff_el[-1]) * \
            self.sim_params.interval_time / 60 / 1000

        # Now convert the load points according to the max. hydrogen input per time step [kg].
        self.bp_bg_consumed_el = [
            this_bp * self.bg_input_max for this_bp in self.bp_load_el]
        self.bp_bg_consumed_th = [
            this_bp * self.bg_input_max for this_bp in self.bp_load_th]

        # Now get the absolute electrical energy values over the load points [Wh].
        self.bp_energy_el = []
        for i_bp in range(len(self.bp_load_el)):
            # Calculate the electrical energy produced at this breaking point [Wh]
            this_energy_el = \
                self.bp_bg_consumed_el[i_bp] * \
                self.bp_eff_el[i_bp] * self.heating_value_bg * 1000
            self.bp_energy_el.append(this_energy_el)

        # Now get the absolute thermal energy values over the load points [Wh].
        self.bp_energy_th = []
        for i_bp in range(len(self.bp_load_th)):
            # Calculate the thermal energy produced at this breaking point [Wh]
            this_energy_th = \
                self.bp_bg_consumed_th[i_bp] * \
                self.bp_eff_th[i_bp] * self.heating_value_bg * 1000
            self.bp_energy_th.append(this_energy_th)

        # While we will create two oemof components, one for thermal energy and
        # one for electrical energy, and make a constraint that both inflows of
        # hydrogen have to be the same, each component will get only half the
        # amount of hydrogen. Therefore we need to make a list of hydrogen
        # consumed that is halfed [kg]
        self.bp_bg_consumed_el_half = [
            this_bp / 2 for this_bp in self.bp_bg_consumed_el]
        self.bp_bg_consumed_th_half = [
            this_bp / 2 for this_bp in self.bp_bg_consumed_th]

        # Save the two models to set constraints later.
        self.model_el = None
        self.model_th = None

    def get_electrical_energy_by_bg(self, bg_consumption):
        """Gets the electrical energy produced by the according biogas production value.

        :param bg_consumption: biogas production value [kg]
        :return: according electrical energy value [Wh]
        """
        # Check the index of this load point.
        this_index = self.bp_bg_consumed_el_half.index(bg_consumption)
        return self.bp_energy_el[this_index]

    def get_thermal_energy_by_bg(self, bg_consumption):
        """Gets the thermal energy produced by the according biogas production value.

        :param bg_consumption: biogas production value [kg]
        :return: according thermal energy value [Wh]
        """
        # Check the index of this load point.
        this_index = self.bp_bg_consumed_th_half.index(bg_consumption)
        return self.bp_energy_th[this_index]

    def create_oemof_model(self, busses, model):
        """Creates two separate oemof Piecewise Linear Transformer components for the
        electrical and thermal production of the biogas CHP from information given
        in the GasEngineChpBiogas class, to be used in the oemof model

        :param busses: virtual buses used in the energy system
        :type busses: list
        :param model: oemof model containing the electrical energy production and
            thermal energy production of the biogas CHP
        :type model: model
        :return: the oemof biogas CHP electric and thermal components
        """
        # Create the non-linear oemof component. The CHP has to be modelled as
        # two components, while the piecewise linear transformer does not
        # accept 2 outputs yet.
        # TODO: adjust once the piecewise linear transformer allows 2 outputs

        flow_electric = solph.Flow(
            nominal_value=self.bp_bg_consumed_el_half[-1],
            variable_costs=0)
        flow_thermal = solph.Flow(nominal_value=self.bp_bg_consumed_el_half[-1])

        # First create the electrical oemof component.
        gas_engine_chp_biogas_electric = solph.custom.PiecewiseLinearTransformer(
            label=self.name + '_electric',
            inputs={busses[self.bus_bg]: flow_electric},
            outputs={busses[self.bus_el]: solph.Flow()},
            in_breakpoints=self.bp_bg_consumed_el_half,
            conversion_function=self.get_electrical_energy_by_bg,
            pw_repn='CC')

        # Then create the thermal oemof component.
        gas_engine_chp_biogas_thermal = solph.custom.PiecewiseLinearTransformer(
            label=self.name + '_thermal',
            inputs={busses[self.bus_bg]: flow_thermal},
            outputs={busses[self.bus_th]: solph.Flow()},
            in_breakpoints=self.bp_bg_consumed_th_half,
            conversion_function=self.get_thermal_energy_by_bg,
            pw_repn='CC')

        # Add the two components to the model.
        model.add(gas_engine_chp_biogas_electric, gas_engine_chp_biogas_thermal)

        self.model_el = gas_engine_chp_biogas_electric
        self.model_th = gas_engine_chp_biogas_thermal

        return None

    def update_constraints(self, busses, model_to_solve):
        """Set a constraint so that the biogas inflow of the electrical and
        the thermal part are always the same (which is necessary while the
        piecewise linear transformer cannot have two outputs yet and
        therefore the two parts need to be separate components).

        :param busses:
        :param model_to_solve: The oemof model that will be solved
        :type model_to_solve: model
        """
        def chp_ratio_rule_methane(model, t):
            """Ensures that the flows going into the biogas CHP electricity production
            component and those going into the biogas CHP thermal energy production
            component are equal.

            :param model: The oemof model containing the electrical energy production and
                thermal energy production of the electrolyser
            :type model: model
            :param t: ?
            :return: expression = 0
            """
            # Inverter flow
            expr = 0
            expr += model.flow[busses[self.bus_bg], self.model_th, t]
            # force discharge to zero when grid available
            expr += - model.flow[busses[self.bus_bg], self.model_el, t]
            return (expr == 0)

        setattr(model_to_solve,
                'chp_flow_ratio_fix_methane_{}'.format(self.name.replace(' ', '')),
                po.Constraint(model_to_solve.TIMESTEPS, rule=chp_ratio_rule_methane)
                )

    def update_flows(self, results):
        """Updates the flows of the biogas CHP components for each time step.

        :param results: The oemof results for the given time step
        :type results: object
        :return: updated flow values for each flow in the 'flows' dict
        """
        # Check if the component has an attribute 'flows', if not, create it as an empty dict.
        Component.update_flows(self, results, self.name + '_electric')
        Component.update_flows(self, results, self.name + '_thermal')
