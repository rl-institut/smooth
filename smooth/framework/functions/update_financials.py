from smooth.framework.functions.fitting_cost import update_cost, get_dependant_value


def update_financials(component, financials):
    # Calculate OPEX or CAPEX for this component.
    # Params:
    #  component: object of this component
    #  financials: financial object of this component. This can be either the "capex" or the "opex" dict.
    #
    # This function is calculating a fix CAPEX and OPEX value for components where CAPEX and OPEX are dependant on
    # certain values. The following list shows possible fitting methods. The fitting method is chosen by the CAPEX and
    # OPEX key:
    #
    # "fix"      --> already the fix value, nothing has to be done
    # "spec"     --> cost value needs to be multiplied with the dependant value
    # "exp"      --> exponential cost fitting
    # "poly"     --> polynomial cost fitting
    # "free"     --> polynomial cost fitting with free choosable exponents
    #
    # If multiple keys are defined, the calculations are done sequentially in order.

    # Check if this financial dictionary is empty. If so, nothing has to be calculated.
    if not financials:
        return

    # If the keys are not given as a list, they are transformed to one so they can be iterated.
    if type(financials['key']) is not list:
        financials['key'] = [financials['key']]
        financials['fitting_value'] = [financials['fitting_value']]
        financials['dependant_value'] = [financials['dependant_value']]

    # Loop through each CAPEX or OPEX key.
    for this_index in range(len(financials['key'])):
        # Get the dependant value (either if given as a component parameter of else it is the previous cost value).
        dependant_value = get_dependant_value(component, financials, this_index, 'capex')
        # Update cost
        update_cost(component, financials, this_index, dependant_value)
