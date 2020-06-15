from smooth.framework.functions.update_fitted_cost import update_financials
from smooth.framework.functions.update_annuities import update_external_annuities


class ExternalComponent:
    """A class created for external components in the system that will not be part of the optimization,
    but the CAPEX and OPEX of these components should still be evaluated"""

    def __init__(self):
        # PARAMETERS
        # Define the external component type
        self.external_component = None
        # Define a name (needs to different from the other names of components in
        # this energy system).
        self.name = None
        # Life time [a].
        self.life_time = None
        # Simulation parameters, like interval time and interest rate.
        self.sim_params = None

        # Initializing results, don't know if I need this yet
        self.results = {}

        # FINANCIALS (CAPEX AND OPEX)
        self.opex = dict()
        self.capex = dict()

    def set_parameters(self, params):
        for this_param in params:
            if not hasattr(self, this_param):
                # Raise an error if the given parameter is not part of the
                # component (interval time is an exception).
                raise ValueError('The parameter "{}" is not part of the '
                                 'component'.format(this_param))

            setattr(self, this_param, params[this_param])

    def generate_results(self):
        # Generate the results after the simulation.

        # Compute the CAPEX and then the OPEX results.
        update_financials(self, self.capex)
        update_financials(self, self.opex)
        # Calculate the annuities of the CAPEX
        update_external_annuities(self)

    def check_validity(self):
        # This function is called immediately after the component object is created and checks
        # if the component attributes are valid.

        # Check if a life time is given when there are CAPEX given.
        if self.capex:
            if self.life_time is None or self.life_time <= 0:
                raise ValueError('In component {} CAPEX or fix_emissions are given'
                                 ' but the life_time is either None or '
                                 'not greater than zero. Please choose another'
                                 ' life_time value!'.format(self.name))
