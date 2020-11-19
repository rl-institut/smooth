from oemof.outputlib import views
from smooth.framework.functions.update_fitted_cost import update_financials, update_emissions
from smooth.framework.functions.update_annuities import update_annuities


class Component:

    def __init__(self):
        # PARAMETERS
        # Define the component type (e.g. "electrolyzer" means component_electrolyzer.py)
        self.component = None
        # Define a name (needs to different from the other names of components
        # in this energy system).
        self.name = None
        # Life time [a].
        self.life_time = None
        # Simulation parameters, like interval time and interest rate.
        self.sim_params = None

        # INITIALIZE VARIABLES EACH COMPONENT WILL HAVE.
        # Initializing results and states as empty dicts.
        self.results = {}
        self.states = {}

        # VARIABLE COSTS
        # Initializing variable cost and art. cost values [EUR/*].
        self.variable_costs = None
        self.artificial_costs = None
        self.dependency_flow_costs = None

        # FINANCIALS (CAPEX AND OPEX)
        self.opex = dict()
        self.capex = dict()

        # Initializing variable emission values [kg/*] and the flow [*] it depends on.
        self.variable_emissions = None
        self.dependency_flow_emissions = None
        # Initializing fixed and operational emission values.
        self.op_emissions = dict()
        self.fix_emissions = dict()

        # FOREIGN STATES
        # Initializing foreign state component name and attribute name, if set
        # both need to be strings.
        self.fs_component_name = None
        self.fs_attribute_name = None

    def set_parameters(self, params):
        for this_param in params:
            if not hasattr(self, this_param):
                # Raise an error if the given parameter is not part of the
                # component (interval time is an exception).
                raise ValueError(
                    'The parameter "{}" is not part of the component'.format(this_param))

            setattr(self, this_param, params[this_param])

        if self.variable_costs is not None or self.artificial_costs is not None:
            assert self.dependency_flow_costs is not None, \
                "If variable (and/or artificial) costs are defined, " \
                "the dependency_flow for costs has to be defined as well."
        if self.variable_emissions is not None:
            assert self.dependency_flow_emissions is not None,\
                "If variable emissions are defined, " \
                "dependency_flow for emissions has to be defined as well."

    # ------------------- UPDATE THE FLOWS FOR EACH COMPONENT -------------------

    def update_flows(self, results, comp_name=None):
        # Check if the component has an attribute 'flows', if not, create it as an empty dict.
        if not hasattr(self, 'flows'):
            self.flows = {}

        # While components can generate more than one oemof model, they
        # sometimes need to give a custom name.
        if comp_name is None:
            comp_name = self.name

        this_comp_node = views.node(results, comp_name)
        this_df = this_comp_node['sequences']
        for i_result in this_df:
            # Check if this result is a flow
            if i_result[1] == 'flow':
                this_flow_name = i_result[0][:]
                # Check if there already is an array to store the flow
                # information, if not, create one.
                if this_flow_name not in self.flows:
                    self.flows[this_flow_name] = [None] * self.sim_params.n_intervals
                # Saving this flow value to the results file
                self.flows[this_flow_name][self.sim_params.i_interval] = this_df[i_result][0]

    # ------------------- PREPARE CREATING THE OEMOF MODEL -------------------

    def prepare_simulation(self, components):
        # If a component has artificial costs, this update_artificial_costs
        # function is overwritten in that component
        pass

    # ------ UPDATE STATES (PLACEHOLDER FOR COMPONENTS WITHOUT STATES) ------

    def update_states(self, results):
        # If a component has states, this update_states function is overwritten in that component
        pass

    def update_constraints(self, busses, model_to_solve):
        # Sometimes special contraints are needed, these can be written here.
        pass

    # ------------------- UPDATE THE COSTS -------------------

    def update_var_costs(self, results):
        # Track the costs and artificial costs of a component for each time step.
        # Parameters:
        #  results: oemof result object for this time step.
        #  self.sim_params: simulation parameters defined by the user.

        # First create an empty cost and art. cost array for this component, if
        # it hasn't been created before.
        if 'variable_costs' not in self.results:
            # If this function is not overwritten in the component, then costs
            # and art. costs are not part of the component and therefore
            # set to 0.
            self.results['variable_costs'] = [0] * self.sim_params.n_intervals
            self.results['art_costs'] = [0] * self.sim_params.n_intervals

        # Update the costs for this time step [EUR].
        if self.variable_costs is not None:
            this_dependency_value = self.flows[self.dependency_flow_costs][
                self.sim_params.i_interval]
            self.results['variable_costs'][self.sim_params.i_interval] = this_dependency_value * \
                self.variable_costs
        # Update the artificial costs for this time step [EUR].
        if self.artificial_costs is not None:
            this_dependency_value = self.flows[self.dependency_flow_costs][
                self.sim_params.i_interval]
            self.results['art_costs'][self.sim_params.i_interval] = this_dependency_value * \
                self.artificial_costs

    def update_var_emissions(self, results):
        # Track the emissions of a component for each time step.
        # Parameters:
        #  results: oemof result object for this time step.
        #  self.sim_params: simulation parameters defined by the user.

        # First create an empty emission array for this component, if it hasn't been created before.
        if 'variable_emissions' not in self.results:
            # If this function is not overwritten in the component, then
            # emissions are not part of the component and therefore set to 0.
            self.results['variable_emissions'] = [0] * self.sim_params.n_intervals

        # Update the emissions for this time step [kg]. Before, verify if a
        # flow name is given as emission dependency.
        if self.variable_emissions is not None:
            this_dependency_value = \
                self.flows[self.dependency_flow_emissions][self.sim_params.i_interval]
            self.results['variable_emissions'][self.sim_params.i_interval] = \
                this_dependency_value * self.variable_emissions

    # ------ ADD COSTS AND ARTIFICIAL COSTS TO A PARAMETER IF THEY ARE NOT NONE ------

    def get_costs_and_art_costs(self):
        # Initialize the total variable costs and art. costs [EUR/???].
        variable_costs_total = 0
        # Add costs and art. costs to an attribute
        if self.variable_costs is not None:
            variable_costs_total += self.variable_costs
        if self.artificial_costs is not None:
            variable_costs_total += self.artificial_costs

        return variable_costs_total

    def get_foreign_state_value(self, components, index=None):
        # Get a foreign state attribute value with the name fs_attribute_name
        # of the component fs_component_name. If the fs_component_name is None
        # and the fs_attribute_name set to a number, the number is given back
        # instead.
        # Parameters:
        #  components: List containing each component object.
        #  index: Index of the foreign state (should be None if there is only
        #  one foreign state) [-].

        if index is None:
            fs_component_name = self.fs_component_name
            fs_attribute_name = self.fs_attribute_name
        else:
            fs_component_name = self.fs_component_name[index]
            fs_attribute_name = self.fs_attribute_name[index]

        # Fixed values also can be used as foreign states. To do that the
        # component name needs to be None and the attribute name needs to be a
        # numeric value (integer of float). This is checked here, and if so,
        # the numeric value is given back.
        if fs_component_name is None and isinstance(fs_attribute_name, (int, float)):
            return fs_attribute_name

        is_fs_found = False
        foreign_state_value = None
        # Loop through all components and find the one containing the foreign state.
        for this_comp in components:
            if this_comp.name is fs_component_name:
                # Get the foreign state value.
                foreign_state_value = this_comp.__getattribute__(fs_attribute_name)
                is_fs_found = True

        if not is_fs_found:
            raise ValueError('Foreign state couldn\'t be found,'
                             'please check the fs names of the supply component.')

        return foreign_state_value

    def generate_results(self):
        # Generate the results after the simulation.

        # Compute the emissions due to installation and operation.
        update_emissions(self, self.fix_emissions)
        update_emissions(self, self.op_emissions)
        # Compute the CAPEX and then the OPEX results.
        update_financials(self, self.capex)
        update_financials(self, self.opex)
        # Calculate the annuities of the CAPEX and the variable costs; and of the emission values
        update_annuities(self)

    def check_validity(self):
        # This function is called immediately after the component object is
        # created and checks if the component attributes are valid.

        # Check if a life time is given when there are CAPEX given.
        if self.capex or self.fix_emissions:
            if self.life_time is None or self.life_time <= 0:
                raise ValueError(
                    'In component {} CAPEX or fix_emissions are given '
                    'but the life_time is either None or not greater than zero. '
                    'Please choose another life_time value!'.format(self.name))
