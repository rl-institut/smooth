from oemof.outputlib import views
from smooth.framework.functions.update_fitted_cost import update_financials, update_emissions
from smooth.framework.functions.update_annuities import update_annuities


class Component:
    """The generic component class is the mother class for all of the components. The parameters and
    functions defined here can be applied to each of the specific components.

    :param component: The component type
    :type component: str
    :param name: The specific name of the component (must be different to other component names in the system)
    :type name: str
    :param life_time: The lifetime of the component [a]
    :type life_time: float
    :param sim_params: The simulation parameters such as the interval time and interest rate
    :type sim_params: object ToDo: check this

    :param results: The dictionary containing the main results for the component
    :type results: dict
    :param states: The dictionary containing the varying states for the component
    :type states: dict

    :param variable_costs: The variable costs of the component [EUR/*]
    :type variable_costs: numeric
    :param artificial_costs: The artificial costs of the component [EUR/*] (Note: these costs are not included in the final financial analysis)
    :type artificial_costs: numeric
    :param dependency_flow_costs: The flow that the costs are dependent on
    :type dependency_flow_costs: str ToDo: maybe this changes with Timo's new pull request?

    :param capex: The capital costs
    :type capex: dict
    :param opex: The operational and maintenance costs
    :type opex: dict

    :param variable_emissions: The variable emissions of the component [kg/*]
    :type variable_emissions: float
    :param dependency_flow_emissions: The flow that the emissions are dependent on
    :type dependency_flow_emissions: str ToDo: maybe this changes with Timo's new pull request?
    :param op_emissions: The operational emission values
    :type op_emissions: dict
    :param fix_emissions: The fixed emission values
    :type fix_emissions: dict

    :param fs_component_name: The foreign state component name
    :type fs_component_name: str
    :param fs_attribute_name: The foreign state attribute name
    :type fs_attribute_name: str

    Notes
    -----
    ToDo: maybe CAPEX/OPEX explanations here? Or outside of component description
    """
    def __init__(self):
        """Constructor method
        """
        self.component = None
        self.name = None
        self.life_time = None
        self.sim_params = None
        self.results = {}
        self.states = {}
        self.variable_costs = None
        self.artificial_costs = None
        self.dependency_flow_costs = None
        self.opex = dict()
        self.capex = dict()
        self.variable_emissions = None
        self.dependency_flow_emissions = None
        self.op_emissions = dict()
        self.fix_emissions = dict()
        self.fs_component_name = None
        self.fs_attribute_name = None

    # ------------------- SET THE PARAMETERS FOR EACH COMPONENT -------------------

    def set_parameters(self, params):
        """Sets the parameters that have been defined by the user (in the model definition) in
        the necessary components, overwriting the default parameter values. Errors are raised if:
        - the given parameter is not part of the component (interval time is an exception)
        - the dependency flows have not been defined

        :param params: The set of parameters defined in the specific component class
        :type params: dict ToDo: make sure of this, maybe list
        :raises ValueError: Value error is raised if the parameter defined by the user
        is not part of the component, or dependency flows are not defined
        :return: None
        """
        for this_param in params:
            if not hasattr(self, this_param):
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

    def update_flows(self, results, sim_params, comp_name=None):
        """Updates the flows of a component for each time step.

        :param results: The oemof results for the given time step
        :type results: object
        :param sim_params: The simulation parameters for the energy system (defined by user)
        :type sim_params: object
        :param comp_name: The name of the component - while components can generate more than one oemof model, they sometimes need to give a custom name, defaults to None
        :type comp_name: str, optional
        :return: updated flow values for each flow in the 'flows' dict
        """
        # Check if the component has an attribute 'flows', if not, create it as an empty dict.
        if not hasattr(self, 'flows'):
            self.flows = {}

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
                    self.flows[this_flow_name] = [None] * sim_params.n_intervals
                # Saving this flow value to the results file
                self.flows[this_flow_name][sim_params.i_interval] = this_df[i_result][0]

    # ------------------- PREPARE CREATING THE OEMOF MODEL -------------------

    def prepare_simulation(self, components):
        """Prepares the simulation. If a component has artificial costs, this
        prepare_simulation function is overwritten in the specific component.

        :param components: List containing each component object
        :type components: list
        :return: If used as a placeholder, nothing will be returned. Else, refer to
            specific component that uses the prepare_simulation function for further detail.
        """
        pass

    # ------------------- UPDATE STATES -------------------

    def update_states(self, results, sim_params):
        """Updates the states, used as placeholder for components without states.
        If a component has states, this update_states function is overwritten in the
        specific component.

        :param results: oemof results object for the given time step
        :type results: object
        :param sim_params: simulation parameters for the energy system (defined by user)
        :type sim_params: object
        :return: if used as a placeholder, nothing will be returned. Else, refer to
        specific component that uses the update_states function for further detail.
        """
        pass

    # -------------- UPDATE CONSTRAINTS (PLACEHOLDER) --------------

    def update_constraints(self, busses, model_to_solve):
        """Sometimes special constraints are required for the specific components,
        which can be written here. Else, this function is used as placeholder for
        components without constraints.

        :param busses: List of the virtual buses used in the energy system
        :type busses: list
        :param model_to_solve: ToDo: look this up in oemof
        :type model_to_solve:
        :return: If used as a placeholder, nothing will be returned. Else, refer to specific component that uses the update_constraints function for further detail.
        """
        pass

    # ------------------- UPDATE THE COSTS -------------------

    def update_var_costs(self, results, sim_params):
        """
        Tracks the cost and artificial costs of a component for each time step.

        :param results: The oemof results object for the given time step
        :type results: object
        :param sim_params: The simulation parameters for the energy system (defined by user)
        :type sim_params: object
        :return: New values for the updated variable and artificial costs stored in results['variable_costs'] and results['art_costs'] respectively
        """


        # First create an empty cost and art. cost array for this component, if
        # it hasn't been created before.
        if 'variable_costs' not in self.results:
            # If this function is not overwritten in the component, then costs
            # and art. costs are not part of the component and therefore
            # set to 0.
            self.results['variable_costs'] = [0] * sim_params.n_intervals
            self.results['art_costs'] = [0] * sim_params.n_intervals

        # Update the costs for this time step [EUR].
        if self.variable_costs is not None:
            this_dependency_value = self.flows[self.dependency_flow_costs][sim_params.i_interval]
            self.results['variable_costs'][sim_params.i_interval] = this_dependency_value * \
                self.variable_costs
        # Update the artificial costs for this time step [EUR].
        if self.artificial_costs is not None:
            this_dependency_value = self.flows[self.dependency_flow_costs][sim_params.i_interval]
            self.results['art_costs'][sim_params.i_interval] = this_dependency_value * \
                self.artificial_costs

    def update_var_emissions(self, results, sim_params):
        """Tracks the emissions of a component for each time step.

        :param results: The oemof results object for the given time step
        :type results: object
        :param sim_params: The simulation parameters for the energy system (defined by user)
        :type sim_params: object
        :return: A new value for the updated emissions stored in results['variable_emissions']
        """
        # First create an empty emission array for this component, if it hasn't been created before.
        if 'variable_emissions' not in self.results:
            # If this function is not overwritten in the component, then
            # emissions are not part of the component and therefore set to 0.
            self.results['variable_emissions'] = [0] * sim_params.n_intervals

        # Update the emissions for this time step [kg]. Before, verify if a
        # flow name is given as emission dependency.
        if self.variable_emissions is not None:
            this_dependency_value = \
                self.flows[self.dependency_flow_emissions][sim_params.i_interval]
            self.results['variable_emissions'][sim_params.i_interval] = \
                this_dependency_value * self.variable_emissions

    # ------ ADD COSTS AND ARTIFICIAL COSTS TO A PARAMETER IF THEY ARE NOT NONE ------

    def get_costs_and_art_costs(self):
        """Initialize the total variable costs and art. costs [EUR/*]

        :return: The total variable costs (including artificial costs)
        """
        variable_costs_total = 0
        # Add costs and art. costs to an attribute
        if self.variable_costs is not None:
            variable_costs_total += self.variable_costs
        if self.artificial_costs is not None:
            variable_costs_total += self.artificial_costs

        return variable_costs_total

    def get_foreign_state_value(self, components, index=None):
        """ Get a foreign state attribute value with the name fs_attribute_name
        of the component fs_component_name. If the fs_component_name is None
        and the fs_attribute_name set to a number, the number is given back instead.

        :param components: List containing each component object
        :type components: object
        :param index: Index of the foreign state (should be None if there is only one foreign state) [-]
        :type index: int, optional
        :return: Foreign state value
        """
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
        """Generates the results after the simulation.

        :return: Results for the calculated emissions, financials and annuities
        """
        # Compute the emissions due to installation and operation.
        update_emissions(self, self.fix_emissions)
        update_emissions(self, self.op_emissions)
        # Compute the CAPEX and then the OPEX results.
        update_financials(self, self.capex)
        update_financials(self, self.opex)
        # Calculate the annuities of the CAPEX and the variable costs; and of the emission values
        update_annuities(self)

    def check_validity(self):
        """This function is called immediately after the component object is created
        and checks if the component attributes are valid.

        :raises ValueError: Value error raised if the life time is not defined or is less than or equal to 0
        """
        # Check if a life time is given when there are CAPEX given.
        if self.capex or self.fix_emissions:
            if self.life_time is None or self.life_time <= 0:
                raise ValueError(
                    'In component {} CAPEX or fix_emissions are given '
                    'but the life_time is either None or not greater than zero. '
                    'Please choose another life_time value!'.format(self.name))
