from smooth.components.component import Component
import oemof.solph as solph
import pyomo.environ as po


class H2Chp(Component):
    """ A combined heat and power plant with a h2 chp, using H2 to generate
    electricity and heat. """

    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        # PARAMETERS TO CHANGE BY THE USER
        self.name = 'H2 CHP default name'

        # Busses (H2 in, electrical out, thermal out).
        self.bus_h2 = None
        self.bus_el = None
        self.bus_th = None

        # Max. electrical output power [W].
        self.power_max = None

        # Update the input parameters by the user.
        self.set_parameters(params)

        # INTERNAL PARAMETERS
        # Heating value of hydrogen [kWh/kg].
        self.heating_value = 33.33

        # The H2 CHP electrical efficiency and a thermal efficiency
        # source https://www.2-g.com/de/wasserstoff-bhkw/

        if self.power_max <= 115e3:
            # Electrical efficiency load break points (e.g. 0.05 --> 5 %) [-]
            self.bp_load_electric = [0.0, 1.0]
            # Electrical efficiency break points (e.g. 0.05 --> 5 %) [-]
            self.bp_eff_electric = [0.377, 0.377]

            # Thermal efficiency load break points (e.g. 0.05 --> 5 %) [-].
            self.bp_load_thermal = [0.0, 1.0]
            # Thermal efficiency break points (e.g. 0.05 --> 5 %) [-].
            self.bp_eff_thermal = [0.423, 0.423]

        elif 115e3 < self.power_max <= 170e3:
            # Electrical efficiency load break points (e.g. 0.05 --> 5 %) [-]
            self.bp_load_electric = [0.0, 1.0]
            # Electrical efficiency break points (e.g. 0.05 --> 5 %) [-]
            self.bp_eff_electric = [0.39, 0.39]

            # Thermal efficiency load break points (e.g. 0.05 --> 5 %) [-].
            self.bp_load_thermal = [0.0, 1.0]
            # Thermal efficiency break points (e.g. 0.05 --> 5 %) [-].
            self.bp_eff_thermal = [0.419, 0.419]

        elif 170e3 < self.power_max <= 240e3:
            # Electrical efficiency load break points (e.g. 0.05 --> 5 %) [-]
            self.bp_load_electric = [0.0, 1.0]
            # Electrical efficiency break points (e.g. 0.05 --> 5 %) [-]
            self.bp_eff_electric = [0.402, 0.402]

            # Thermal efficiency load break points (e.g. 0.05 --> 5 %) [-].
            self.bp_load_thermal = [0.0, 1.0]
            # Thermal efficiency break points (e.g. 0.05 --> 5 %) [-].
            self.bp_eff_thermal = [0.419, 0.419]

        elif 240e3 < self.power_max:
            # Electrical efficiency load break points (e.g. 0.05 --> 5 %) [-]
            self.bp_load_electric = [0.0, 1.0]
            # Electrical efficiency break points (e.g. 0.05 --> 5 %) [-]
            self.bp_eff_electric = [0.405, 0.405]

            # Thermal efficiency load break points (e.g. 0.05 --> 5 %) [-].
            self.bp_load_thermal = [0.0, 1.0]
            # Thermal efficiency break points (e.g. 0.05 --> 5 %) [-].
            self.bp_eff_thermal = [0.417, 0.417]

        # Now calculate the absolute values for electricity [Wh] and thermal
        # energy [Wh] and H2 consumption [kg].

        # Therefor first calculate the max. hydrogen input that lead to the
        # max. electrical energy in Wh [kg].
        self.h2_input_max = self.power_max / (
            self.heating_value * self.bp_eff_electric[-1]) * \
            self.sim_params.interval_time / 60 / 1000

        # Now convert the load points according to the max. hydrogen input per time step [kg].
        self.bp_h2_consumed_electric = [
            this_bp * self.h2_input_max for this_bp in self.bp_load_electric]
        self.bp_h2_consumed_thermal = [
            this_bp * self.h2_input_max for this_bp in self.bp_load_thermal]

        # Now get the absolute electrical energy values over the load points [Wh].
        self.bp_energy_electric = []
        for i_bp in range(len(self.bp_load_electric)):
            # Calculate the electrical energy produced at this breaking point [Wh]
            this_energy_electric = \
                self.bp_h2_consumed_electric[i_bp] * \
                self.bp_eff_electric[i_bp] * self.heating_value * 1000
            self.bp_energy_electric.append(this_energy_electric)

        # Now get the absolute thermal energy values over the load points [Wh].
        self.bp_energy_thermal = []
        for i_bp in range(len(self.bp_load_thermal)):
            # Calculate the thermal energy produced at this breaking point [Wh]
            this_energy_thermal = \
                self.bp_h2_consumed_thermal[i_bp] * \
                self.bp_eff_thermal[i_bp] * self.heating_value * 1000
            self.bp_energy_thermal.append(this_energy_thermal)

        # While we will create two oemof components, one for thermal energy and
        # one for electrical energy, and make a constraint that both inflows of
        # hydrogen have to be the same, each component will get only half the
        # amount of hydrogen. Therefore we need to make a list of hydrogen
        # consumed that is halfed [kg]
        self.bp_h2_consumed_electric_half = [
            this_bp / 2 for this_bp in self.bp_h2_consumed_electric]
        self.bp_h2_consumed_thermal_half = [this_bp / 2 for this_bp in self.bp_h2_consumed_thermal]

        # Save the two models to set constraints later.
        self.model_el = None
        self.model_th = None

    def get_electrical_energy_by_h2(self, h2_consumption):
        # Check the index of this load point.
        this_index = self.bp_h2_consumed_electric_half.index(h2_consumption)
        # Return the according hydrogen production value [kg].
        return self.bp_energy_electric[this_index]

    def get_thermal_energy_by_h2(self, h2_consumption):
        # Check the index of this load point.
        this_index = self.bp_h2_consumed_thermal_half.index(h2_consumption)
        # Return the according hydrogen production value [kg].
        return self.bp_energy_thermal[this_index]

    def create_oemof_model(self, busses, model):
        # Create the non-linear oemof component. The CHP has to be modelled as
        # two components, while the piecewise linear transformer does not
        # accept 2 outputs yet.

        flow_electric = solph.Flow(
            nominal_value=self.bp_h2_consumed_electric_half[-1],
            variable_costs=0)
        flow_thermal = solph.Flow(nominal_value=self.bp_h2_consumed_electric_half[-1])

        # First create the electrical oemof component.
        h2_chp_electric = solph.custom.PiecewiseLinearTransformer(
            label=self.name+'_electric',
            inputs={busses[self.bus_h2]: flow_electric},
            outputs={busses[self.bus_el]: solph.Flow()},
            in_breakpoints=self.bp_h2_consumed_electric_half,
            conversion_function=self.get_electrical_energy_by_h2,
            pw_repn='CC')

        # Then create the thermal oemof component.
        h2_chp_thermal = solph.custom.PiecewiseLinearTransformer(
            label=self.name+'_thermal',
            inputs={busses[self.bus_h2]: flow_thermal},
            outputs={busses[self.bus_th]: solph.Flow()},
            in_breakpoints=self.bp_h2_consumed_thermal_half,
            conversion_function=self.get_thermal_energy_by_h2,
            pw_repn='CC')

        # Add the two components to the model.
        model.add(h2_chp_electric, h2_chp_thermal)

        self.model_el = h2_chp_electric
        self.model_th = h2_chp_thermal

        """
        # Get the input H2 flows of both oemof components that need to be set equal.
        flow_electric = model.nodes[len(model.nodes)-2].inputs[busses[self.bus_h2]]
        flow_thermal = model.nodes[len(model.nodes) - 1].inputs[busses[self.bus_h2]]

        # Get
        fl_el = model.groups[self.name + '_electric'].inputs[busses[self.bus_h2]]
        fl_th = model.groups[self.name + '_thermal'].inputs[busses[self.bus_h2]]
        """
        # Now set the two inflows of H2 in the electrical in the thermal CHP
        # component to be the same.
        # solph.constraints.equate_variables(model, flow_electric, flow_thermal)

        return None

    def update_constraints(self, busses, model_to_solve):
        # Set a constraint so that the hydrogen inflow of the electrical and
        # the thermal part are always the same (which is necessary while the
        # piecewise linear transformer cannot have two outputs yet and
        # therefore the two parts need to be separate components).
        def chp_ratio_rule(model, t):
            # Inverter flow
            expr = 0
            expr += model.flow[busses[self.bus_h2], self.model_th, t]
            # force discharge to zero when grid available
            expr += - model.flow[busses[self.bus_h2], self.model_el, t]
            return (expr == 0)

        setattr(model_to_solve,
                'chp_flow_ratio_fix_{}'.format(self.name.replace(' ', '')),
                po.Constraint(model_to_solve.TIMESTEPS, rule=chp_ratio_rule)
                )

    def update_flows(self, results, sim_params):
        # Check if the component has an attribute 'flows', if not, create it as an empty dict.
        Component.update_flows(self, results, sim_params, self.name + '_electric')
        Component.update_flows(self, results, sim_params, self.name + '_thermal')
