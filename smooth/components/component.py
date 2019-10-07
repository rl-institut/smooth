from oemof.outputlib import views
from smooth.framework.functions.update_financials import update_financials


class Component:

    def __init__(self):
        # INITIALIZE VARIABLES EACH COMPONENT WILL HAVE.
        # Initializing results and states as empty dicts.
        self.results = {}
        self.states = {}

        # VARIABLE COSTS
        # Initializing variable cost and art. cost values [EUR/???].
        self.variable_costs = None
        self.variable_artificial_costs = None

        # FINANCIALS (CAPEX AND OPEX)
        self.opex = dict()
        self.capex = dict()
        # Initializing CAPEX costs.
        # The CAPEX costs can be either fix [EUR] or dependant [EUR/???]. For more details see capex_cost_key.
        self.capex['cost'] = 0
        # Investment costs can either be a fixed price or they can be dependant on a
        # parameter of the component. If the capex costs are a fixed price, the capex_cost_key has to be set to fix
        # (which is the default value). Other options of the capex_cost_key are:
        #
        # "fix"      --> already the fix value, nothing has to be done
        # "spec"     --> cost value needs to be multiplied with the dependant value
        # "exp"      --> exponential cost fitting
        # "poly"     --> polynomial cost fitting
        # "free"     --> polynomial cost fitting with free choosable exponents
        #
        # A description for each fitting function can be found in smooth.framework.functions.update_financials.py
        #
        # NOTE ON MULTIPLE KEYS:
        # Sometimes the a fitting method is used to get a specific value, in this case multiple keys and fitting values
        # can be given. The dependant value will only be used for the first key, after that, the costs from the last
        # cost calculation is used as the dependant value.

        self.capex['key'] = 'fix'
        # If the key is not fixed, the actual cost depend on a dependant value, that is defined here.
        self.capex['dependant_value'] = None
        # Depending on the method the costs depend on, fitting values might be needed.
        self.capex['fitting_value'] = None
        # Initializing OPEX costs.
        # The OPEX costs can be either fix [EUR/a] or dependant [EUR/(a*???)]. For more details see opex_cost_key.
        self.opex['cost'] = 0
        # Same as key description for the capex key (see above).
        self.opex['key'] = 'fix'
        # If the key is not fixed, the actual cost depend on a dependant value, that is defined here.
        self.opex['dependant_value'] = None
        # Depending on the method the costs depend on, fitting values might be needed.
        self.opex['fitting_value'] = None

        # FOREIGN STATES
        # Initializing foreign state component name and attribute name, if set both need to be strings.
        self.fs_component_name = None
        self.fs_attribute_name = None

    def set_parameters(self, params):
        for this_param in params:
            if not hasattr(self, this_param) and this_param is not 'interval_time':
                # Raise an error if the given parameter is not part of the component (interval time is an exception).
                raise ValueError('The parameter "{}" is not part of the component'.format(this_param))

            setattr(self, this_param, params[this_param])

    """ UPDATE THE FLOWS FOR EACH COMPONENT """
    def update_flows(self, results, sim_params):
        # Check if the component has an attribute 'flows', if not, create it as an empty dict.
        if not hasattr(self, 'flows'):
            self.flows = {}

        this_comp_node = views.node(results, self.name)
        this_df = this_comp_node['sequences']
        for i_result in this_df:
            # Check if this result is a flow
            if i_result[1] == 'flow':
                this_flow_name = 'flow: ' + i_result[0][0] + '-->' + i_result[0][1]
                # Check if there already is an array to store the flow information, if not, create one.
                if this_flow_name not in self.flows:
                    self.flows[this_flow_name] = [None] * sim_params.n_intervals
                # Saving this flow value to the results file
                self.flows[this_flow_name][sim_params.i_interval] = this_df[i_result][0]

    """ PREPARE CREATING THE OEMOF MODEL """
    def prepare_simulation(self, components):
        # If a component has artificial costs, this update_artificial_costs function is overwritten in that component
        pass

    """ UPDATE STATES (PLACEHOLDER FOR COMPONENTS WITHOUT STATES) """
    def update_states(self, results, sim_params):
        # If a component has states, this update_states function is overwritten in that component
        pass

    """ UPDATE THE COSTS """
    def update_costs(self, results, sim_params, this_dependant_value=0):
        # Track the costs and artificial costs of a component for each time step.
        # Parameters:
        #  results: oemof result object for this time step.
        #  sim_params: simulation parameters defined by the user.
        #  this_dependant_value: Value the costs depend on for this time step (e.g. this might be electricity sold by a
        #    grid in Wh, then the values variable_costs and variable_artificial_costs need to be in EUR/Wh)

        # First create an empty cost and art. cost array for this component, if it hasn't been created before.
        if 'costs' not in self.results:
            # If this function is not overwritten in the component, then costs and art. costs are not part of the
            # component and therefore set to 0.
            self.results['costs'] = [0] * sim_params.n_intervals
            self.results['art_costs'] = [0] * sim_params.n_intervals

        # Update the costs for this time step [EUR].
        if self.variable_costs is not None:
            self.results['costs'][sim_params.i_interval] = this_dependant_value * self.variable_costs
        # Update the artificial costs for this time step [EUR].
        if self.variable_artificial_costs is not None:
            self.results['art_costs'][sim_params.i_interval] = this_dependant_value * self.variable_artificial_costs

    """ ADD COSTS AND ARTIFICIAL COSTS TO A PARAMTER IF THEY ARE NOT NONE """
    def get_costs_and_art_costs(self):
        # Initialize the total variable costs and art. costs [EUR/???].
        variable_costs_total = 0
        # Add costs and art. costs to an attribute
        if self.variable_costs is not None:
            variable_costs_total += self.variable_costs
        if self.variable_artificial_costs is not None:
            variable_costs_total += self.variable_artificial_costs

        return variable_costs_total

    def get_foreign_state_value(self, components):
        # Get a foreign state attribute value with the name fs_attribute_name of the component fs_component_name.
        # Parameters:
        #  components: List containing each component object.

        is_fs_found = False
        foreign_state_value = None
        # Loop through all components and find the one containing the foreign state.
        for this_comp in components:
            if this_comp.name is self.fs_component_name:
                # Get the foreign state value.
                foreign_state_value = this_comp.__getattribute__(self.fs_attribute_name)
                is_fs_found = True

        if not is_fs_found:
            raise ValueError('Foreign state couldn\'t be found, please check the fs names of the supply component.')

        return foreign_state_value

    def generate_results(self):
        # Generate the results after the simulation.
        update_financials(self)







