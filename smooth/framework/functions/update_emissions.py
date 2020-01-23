import math

def update_emissions(component, emissions):
    # Calculate OPEX or CAPEX for this component.
    # Params:
    #  component: object of this component
    #  emissions: emission object of this component. This can be either the "fix_emissions" or the "op_emissions" dict.
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

    # Check if this emission dictionary is empty. If so, nothing has to be calculated.
    if not emissions:
        return

    # If the keys are not given as a list, they are transformed to one so they can be iterated.
    if type(emissions['key']) is not list:
        emissions['key'] = [emissions['key']]
        emissions['fitting_value'] = [emissions['fitting_value']]
        emissions['dependant_value'] = [emissions['dependant_value']]

    # Loop through each CAPEX or OPEX key.
    for this_index in range(len(emissions['key'])):
        update_cost(component, emissions, this_index)


def update_cost(component, emissions, index):
    this_key = emissions['key'][index]
    if this_key == 'fix':
        # Fixed costs do not have to be processed further.
        pass
    elif this_key == 'spec':
        update_spec(component, emissions, index)
    elif this_key == 'exp':
        update_exp(component, emissions, index)
    elif this_key == 'poly':
        update_poly(component, emissions, index)
    elif this_key == 'free':
        update_free(component, emissions, index)
    else:
        raise ValueError('CAPEX or OPEX key {} not recognized. Please choose a valid key.'.format(this_key))


def update_spec(component, emissions, index):
    # Case: The fitting value is multiplied with the dependant value to get the costs.

    # Get the dependant value (either if given as a component parameter of else it is the previous cost value).
    dependant_value = get_dependant_value(component, emissions, index)
    # Get the fitting value, which is the current cost if "cost" is chosen.
    if emissions['fitting_value'][index] == 'cost':
        fitting_value = emissions['cost']
    else:
        fitting_value = emissions['fitting_value'][index]
    # Calculate the costs [EUR].
    emissions['cost'] = dependant_value * fitting_value


def update_exp(component, emissions, index):
    # Case: An exponential fitting of the cost function is wanted. Here 3 variables are used in the following order:
    # Function if 3 fitting parameters are given:
    # fv_1 + fv_2*exp(fv_3*Parameter)
    # Function if 2 fitting parameters are given:
    # fv_1*exp(fv_2)

    # Get the dependant value (either if given as a component parameter of else it is the previous cost value).
    dependant_value = get_dependant_value(component, emissions, index)

    # Get the fitting values.
    fv = emissions['fitting_value'][index]

    if len(fv) == 2:
        # If only two fitting values are given, it is assumed that the constant value is 0.
        fv = [0, *fv]
    # Calculate the costs [EUR].
    emissions['cost'] = fv[0] + fv[1] * math.exp(fv[2] * dependant_value)


def update_poly(component, emissions, index):
    # Case: An polynomial fitting of the cost function is wanted. In this case, an arbitrary number of fitting
    # parameters can be given. They will be used in the following order:
    # Fitting values fv_1, fv_2, fv_3, ..... fv_n.
    # Function:
    # fv_1 + fv_2*dependant_value + fv_3*dependant_value^2 + ... fv_n*dependant_value^(n-1)

    # Get the dependant value (either if given as a component parameter of else it is the previous cost value).
    dependant_value = get_dependant_value(component, emissions, index)

    # Get the fitting values.
    fv = emissions['fitting_value'][index]
    # Get the number of fitting values [-].
    n_fv = len(fv)

    # In a loop, calculate the costs [EUR].
    cost = 0
    for i_fv in range(n_fv):
        cost += fv[i_fv] * dependant_value ** i_fv

    emissions['cost'] = cost


def update_free(component, emissions, index):
    # Case: An "free" fitting of the cost function is wanted. In this case, an arbitrary number of fitting parameters
    # can be given. They will be used in the following order:
    # Fitting values fv_1, fv_2, fv_3, ..... fv_n.
    # Function:
    # fv_1*dependant_value^fv_2 + fv_3*dependant_value^fv_4 + ... fv_(n-1)*dependant_value^fv_n

    # Get the dependant value (either if given as a component parameter of else it is the previous cost value).
    dependant_value = get_dependant_value(component, emissions, index)

    # Get the fitting values.
    fv = emissions['fitting_value'][index]
    # Get the number of fitting values [-].
    n_fv = len(fv)

    # The number of fitting values needs to be even, otherwise throw an error.
    if n_fv % 2 != 0:
        raise ValueError('In component {}, the number of fitting values is {}, but it needs to be even!'.format(
            component['name'], n_fv))

    # Cost value [EUR]
    cost = 0
    for i in range(int(n_fv/2)):
        cost += fv[i*2] * dependant_value**fv[i*2 + 1]

    # Save the costs [EUR].
    emissions['cost'] = cost


def get_dependant_value(component, emissions, index):
    # Get an attribute of the component as the dependant value.
    dependant_value = getattr(component, emissions['dependant_value'][index])
    if emissions['dependant_value'][index] == 'fix_emissions':
        # If the fix_emissions are chosen as the dependant value, the fix_emissions costs are meant.
        dependant_value = dependant_value['cost']

    return dependant_value



