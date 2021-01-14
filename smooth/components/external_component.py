"""
This class is created for external components in the system that will not be part of the
optimization, but the CAPEX and OPEX of these components should still be evaluated.

******
Scope
******
External components are used in the framework to represent components that do not need
to be included in the simulation/optimization, but nevertheless the annuities in terms
of costs and emissions for the component should be considered. The generic
ExternalComponent class is the mother class for the other external components, providing
a basis for what all external components must have.

*******
Concept
*******
The costs (CAPEX and OPEX) and emissions of the external component are first calculated
(see the :func:`~smooth.framework.functions.update_fitted_cost.update_financials` and
:func:`~smooth.framework.functions.update_fitted_cost.update_emissions` functions), and
then the annuities are calculated using the
:func:`~smooth.framework.functions.update_annuities.update_external_annuities` function.
It should be noted that these costs are not considered in the optimization results as
they are evaluated seperately.
"""

from smooth.framework.functions.update_fitted_cost import update_financials, update_emissions
from smooth.framework.functions.update_annuities import update_external_annuities


class ExternalComponent:
    """
    :param external_component: external component type
    :type external_component: str
    :param name: specific name of the external component (must be unique)
    :type name: str
    :param life_time: lifetime of the external component [a]
    :type life_time: numerical
    :param sim_params: simulation parameters such as the interval time and interest rate
    :type sim_params: object
    :param results: dictionary containing the main results for the component
    :type results: dict
    :param capex: capital costs
    :type capex: dict
    :param opex: operational and maintenance costs
    :type opex: dict
    :param op_emissions: operational emission values
    :type op_emissions: dict
    :param fix_emissions: fixed emission values
    :type fix_emissions: dict
    """

    def __init__(self):
        # ------------------- PARAMETERS -------------------
        self.external_component = None
        self.name = None
        self.life_time = None
        self.sim_params = None
        self.results = {}
        self.capex = dict()
        self.opex = dict()
        self.op_emissions = dict()
        self.fix_emissions = dict()

    def set_parameters(self, params):
        """Sets the parameters that have been defined by the user (in the model definition) in
        the necessary components, overwriting the default parameter values. Errors are raised if:
        - the given parameter is not part of the component

        :param params: The set of parameters defined in the specific external component class
        :type params: dict ToDo: make sure of this, maybe list
        :raises ValueError: Value error is raised if the parameter defined by the user
        is not part of the external component
        :return: None
        """
        for this_param in params:
            if not hasattr(self, this_param):
                # Raise an error if the given parameter is not part of the
                # component (interval time is an exception).
                raise ValueError('The parameter "{}" is not part of the '
                                 'component'.format(this_param))

            setattr(self, this_param, params[this_param])

    def generate_results(self):
        """Generates the results after the simulation.

        :return: Results for the calculated emissions, financials and annuities
        """
        # Compute the CAPEX and then the OPEX results.
        update_financials(self, self.capex)
        update_financials(self, self.opex)
        # Compute the emissions due to installation and operation.
        update_emissions(self, self.fix_emissions)
        update_emissions(self, self.op_emissions)
        # Calculate the annuities of the CAPEX
        update_external_annuities(self)

    def check_validity(self):
        """This function is called immediately after the component object is created
        and checks if the component attributes are valid.

        :raises ValueError: Value error raised if the life time is not defined or is less
            than or equal to 0
        """
        # Check if a life time is given when there are CAPEX given.
        if self.capex or self.fix_emissions:
            if self.life_time is None or self.life_time <= 0:
                raise ValueError('In component {} CAPEX or fix_emissions are given'
                                 ' but the life_time is either None or '
                                 'not greater than zero. Please choose another'
                                 ' life_time value!'.format(self.name))
