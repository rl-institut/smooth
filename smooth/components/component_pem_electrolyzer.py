import oemof.solph as solph
from .component import Component
import pyomo.environ as po


class PemElectrolyzer(Component):
    """ PEM Electrolyzer agents are created through this class """

    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)

        """ PARAMETERS """
        self.name = 'PEM_electrolyzer_default_name'

        # Define the busses (electricity in, h2 out, thermal out).
        self.bus_el = None
        self.bus_h2 = None
        self.bus_th = None

        # Max. electrical input power [W].
        self.power_max = 6000000

        # pressure of hydrogen in the system in [Pa]
        self.pressure = 35 * 10e5  # CHECK WHERE TO INCLUDE (IF NEEDED)
        # Initial temperature [K].
        self.temp_init = 273.15 + 25  # CHECK WHERE TO INCLUDE (IF NEEDED)
        # Life time [a].
        self.life_time = 10

        # Update the input parameters by the user.
        self.set_parameters(params)

        # INTERNAL PARAMETERS
        # Heating value of hydrogen [kWh/kg].
        self.heating_value = 33.33

        # The efficiency curve for the system efficiency over the load point of a PEM
        # electrolyzer, according to:
        # Waidhas, M. 'Electrolyzer technology - the Siemens view' 2016.
        # http://www.scandinavianhydrogen.org/wp-content/uploads/2016/11/2_Manfred-Waidhas.pdf

        # System efficiency load break points in terms of hydrogen production
        # (e.g. 0.05 --> 5 %) [-]
        self.bp_load_h2_prod = [0.0255, 0.0398, 0.0582, 0.0797, 0.0991, 0.1267, 0.1624, 0.2257,
                                0.3565, 0.4545, 0.5832, 0.6803, 0.8151, 0.9418, 1.0]

        # System efficiency break points in terms of hydrogen production
        # (e.g. 0.05 --> 5 %) [-]
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
        # Check the index of this load point.
        this_index = self.bp_elec_consumed_h2_prod_half.index(electricity_consumption)
        # Return the according hydrogen production value [kg].
        return self.bp_h2_production[this_index]

    def get_waste_heat_energy_by_electricity(self, electricity_consumption):
        # Check the index of this load point.
        this_index = self.bp_elec_consumed_waste_heat_half.index(electricity_consumption)
        # Return the according waste heat energy value [Wh]
        return self.bp_waste_heat_energy[this_index]

    def create_oemof_model(self, busses, model):
        # Create the non-linear oemof component.
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
        # Set a constraint so that the electricity inflow of the
        # hydrogen production and the waste heat energy part are
        # always the same (which is necessary while the piecewise
        # linear transformer cannot have two outputs yet and
        # therefore the two parts need to be separate components).
        def electrolyzer_ratio_rule(model, t):
            # Inverter flow
            expr = 0
            expr += model.flow[busses[self.bus_el], self.model_th, t]
            expr += - model.flow[busses[self.bus_el], self.model_h2, t]
            return (expr == 0)

        setattr(model_to_solve,
                'electrolyzer_flow_ratio_fix_{}'.format(self.name.replace(' ', '')),
                po.Constraint(model_to_solve.TIMESTEPS, rule=electrolyzer_ratio_rule)
                )

    def update_flows(self, results):
        # Check if the component has an attribute 'flows', if not, create it as an empty dict.
        Component.update_flows(self, results, self.name + '_h2_prod')
        Component.update_flows(self, results, self.name + '_waste_heat')
