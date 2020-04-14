from smooth.components.component import Component
import oemof.solph as solph
import pyomo.environ as po


class GasEngineChpBiogas(Component):
    """ A combined heat and power plant with a gas engine, using biogas to generate electricity and heat. """

    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)

        """ PARAMETERS """
        # PARAMETERS TO CHANGE BY THE USER
        self.name = 'Gas Engine CHP Biogas default name'

        # Busses (ch4 in, electrical out, thermal out).
        self.bus_ch4 = None
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
        # [kWh/kg] https://www.linde-gas.at/de/images/1007_rechnen_sie_mit_wasserstoff_v110_tcm550-169419.pdf
        self.heating_value_ch4 = 13.9

        # mol masses ch4 and co2
        self.mol_mass_ch4 = 0.01604  # [kg/mol]
        self.mol_mass_co2 = 0.04401  # [kg/mol]

        # Heating value of biogas [kWh/kg].
        # The gas composition is given as a mol percentage. In the following this percentage will be transformed into a
        # mass percentage and finally into the heating value of the biogas by multiplying it with the LHV of CH4
        self.heating_value_biogas = ((self.ch4_share * self.mol_mass_ch4) / ((self.ch4_share*self.mol_mass_ch4) +
                                                                             (self.co2_share*self.mol_mass_co2))) * self.heating_value_ch4

        # The CHP an electrical efficiency and a thermal efficiency
        # Source: 2G Energy AG Technical specification agenitor 206 BG, http://www.n2ies.com/pdf/2g-agenitor.pdf
        # Electrical efficiency load break points (e.g. 0.05 --> 5 %) [-]
        self.bp_load_electric = [0, 0.5, 0.75, 1.0]
        # Electrical efficiency break points (e.g. 0.05 --> 5 %) [-]
        self.bp_eff_electric = [0, 0.349, 0.370, 0.387]

        # Thermal efficiency load break points (e.g. 0.05 --> 5 %) [-].
        self.bp_load_thermal = [0, 0.5, 0.75, 1.0]
        # Thermal efficiency break points (e.g. 0.05 --> 5 %) [-].
        self.bp_eff_thermal = [0, 0.459, 0.438, 0.427]

        # Now calculate the absolute values for electricity [Wh] and thermal energy [Wh] and ch4 consumption [kg].

        # Therefor first calculate the max. biomethane input that lead to the max. electrical energy in Wh [kg].
        self.ch4_input_max = self.power_max / (
            self.heating_value_biogas * self.bp_eff_electric[-1]) * self.sim_params.interval_time / 60 / 1000

        # Now convert the load points according to the max. hydrogen input per time step [kg].
        self.bp_ch4_consumed_electric = [
            this_bp * self.ch4_input_max for this_bp in self.bp_load_electric]
        self.bp_ch4_consumed_thermal = [
            this_bp * self.ch4_input_max for this_bp in self.bp_load_thermal]

        # Now get the absolute electrical energy values over the load points [Wh].
        self.bp_energy_electric = []
        for i_bp in range(len(self.bp_load_electric)):
            # Calculate the electrical energy produced at this breaking point [Wh]
            this_energy_electric = \
                self.bp_ch4_consumed_electric[i_bp] * \
                self.bp_eff_electric[i_bp] * self.heating_value_biogas * 1000
            self.bp_energy_electric.append(this_energy_electric)

        # Now get the absolute thermal energy values over the load points [Wh].
        self.bp_energy_thermal = []
        for i_bp in range(len(self.bp_load_thermal)):
            # Calculate the thermal energy produced at this breaking point [Wh]
            this_energy_thermal = \
                self.bp_ch4_consumed_thermal[i_bp] * \
                self.bp_eff_thermal[i_bp] * self.heating_value_biogas * 1000
            self.bp_energy_thermal.append(this_energy_thermal)

        # While we will create two oemof components, one for thermal energy and one for electrical energy, and make a
        # constraint that both inflows of hydrogen have to be the same, each component will get only half the amount of
        # hydrogen. Therefore we need to make a list of hydrogen consumed that is halfed [kg]
        self.bp_ch4_consumed_electric_half = [
            this_bp / 2 for this_bp in self.bp_ch4_consumed_electric]
        self.bp_ch4_consumed_thermal_half = [
            this_bp / 2 for this_bp in self.bp_ch4_consumed_thermal]

        # Save the two models to set constraints later.
        self.model_el = None
        self.model_th = None

    def get_electrical_energy_by_ch4(self, ch4_consumption):
        # Check the index of this load point.
        this_index = self.bp_ch4_consumed_electric_half.index(ch4_consumption)
        # Return the according hydrogen production value [kg].
        return self.bp_energy_electric[this_index]

    def get_thermal_energy_by_ch4(self, ch4_consumption):
        # Check the index of this load point.
        this_index = self.bp_ch4_consumed_thermal_half.index(ch4_consumption)
        # Return the according hydrogen production value [kg].
        return self.bp_energy_thermal[this_index]

    def create_oemof_model(self, busses, model):
        # Create the non-linear oemof component. The CHP has to be modelled as two components, while the piecewise
        # linear transformer does not accept 2 outputs yet.
        # ToDo: adjust once the piecewise linear transformer allows 2 outputs

        flow_electric = solph.Flow(
            nominal_value=self.bp_ch4_consumed_electric_half[-1],
            variable_costs=0)
        flow_thermal = solph.Flow(nominal_value=self.bp_ch4_consumed_electric_half[-1])

        # First create the electrical oemof component.
        gas_engine_chp_biogas_electric = solph.custom.PiecewiseLinearTransformer(
            label=self.name+'_electric',
            inputs={busses[self.bus_ch4]: flow_electric},
            outputs={busses[self.bus_el]: solph.Flow()},
            in_breakpoints=self.bp_ch4_consumed_electric_half,
            conversion_function=self.get_electrical_energy_by_ch4,
            pw_repn='CC')

        # Then create the thermal oemof component.
        gas_engine_chp_biogas_thermal = solph.custom.PiecewiseLinearTransformer(
            label=self.name+'_thermal',
            inputs={busses[self.bus_ch4]: flow_thermal},
            outputs={busses[self.bus_th]: solph.Flow()},
            in_breakpoints=self.bp_ch4_consumed_thermal_half,
            conversion_function=self.get_thermal_energy_by_ch4,
            pw_repn='CC')

        # Add the two components to the model.
        model.add(gas_engine_chp_biogas_electric, gas_engine_chp_biogas_thermal)

        self.model_el = gas_engine_chp_biogas_electric
        self.model_th = gas_engine_chp_biogas_thermal

        """
        # Get the input ch4 flows of both oemof components that need to be set equal.
        flow_electric = model.nodes[len(model.nodes)-2].inputs[busses[self.bus_ch4]]
        flow_thermal = model.nodes[len(model.nodes) - 1].inputs[busses[self.bus_ch4]]

        # Get
        fl_el = model.groups[self.name + '_electric'].inputs[busses[self.bus_ch4]]
        fl_th = model.groups[self.name + '_thermal'].inputs[busses[self.bus_ch4]]
        """
        # Now set the two inflows of ch4 in the electrical in the thermal CHP component to be the same.
        # solph.constraints.equate_variables(model, flow_electric, flow_thermal)

        return None

    def update_constraints(self, busses, model_to_solve):
        # Set a constraint so that the ch4 inflow of the electrical and the thermal part are always the same (which
        # is necessary while the piecewise linear transformer cannot have two outputs yet and therefore the two parts
        # need to be separate components).
        def chp_ratio_rule_methane(model, t):
            # Inverter flow
            expr = 0
            expr += model.flow[busses[self.bus_ch4], self.model_th, t]
            # force discharge to zero when grid available
            expr += - model.flow[busses[self.bus_ch4], self.model_el, t]
            return (expr == 0)

        model_to_solve.chp_flow_ratio_fix_methane = po.Constraint(
            model_to_solve.TIMESTEPS, rule=chp_ratio_rule_methane)

    def update_flows(self, results, sim_params):
        # Check if the component has an attribute 'flows', if not, create it as an empty dict.
        Component.update_flows(self, results, sim_params, self.name + '_electric')
        Component.update_flows(self, results, sim_params, self.name + '_thermal')
