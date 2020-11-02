import math
from smooth.framework.functions.functions import choose_valid_dict


def update_financials(component, financials):
    """ Calculate "OPEX" or "CAPEX" for this component.

    This function is calculating a fix "CAPEX" and "OPEX" value for components
    where "CAPEX" and "OPEX" are dependant on certain values. The following list
    shows possible fitting methods. The fitting method is chosen by the "CAPEX"
    and "OPEX" key:

    * "fix"      --> already the fix value, nothing has to be done
    * "spec"     --> cost value needs to be multiplied with the dependant value
    * "exp"      --> exponential cost fitting
    * "poly"     --> polynomial cost fitting
    * "free"     --> polynomial cost fitting with free choosable exponents

    If multiple keys are defined, the calculations are done sequentially in order.

     * "variable" --> definition of multiple "CAPEX" or "OPEX" structures:
    If the cost structure changes over the size of a specific value of the component, for example because of the
    effects of economics of scale, the special key "variable" can be used to define multiple "CAPEX" or "OPEX" dicts for
    different ranges of this value

    :param component: object of this component
    :type component: :class:`~smooth.components.component.Component`
    :param financials: financial object of this component
    :type financials: capex or opex dict
    """

    # Check if this financial dictionary is empty. If so, nothing has to be calculated.
    if not financials:
        return

    # Check if 'variable' capex are beeing used, if so decide which capex is valid
    if financials['key'] == 'variable':
        financials = choose_valid_dict(component, financials)

    # If the keys are not given as a list, they are transformed to one so they can be iterated.
    if type(financials['key']) is not list:
        financials['key'] = [financials['key']]
        financials['fitting_value'] = [financials['fitting_value']]
        financials['dependant_value'] = [financials['dependant_value']]

    # Loop through each CAPEX or OPEX key.
    for this_index in range(len(financials['key'])):
        # Get the dependant value (either given as a component value
        # or if dependant value key at this_index is cost 'capex' get the
        # previously calculated cost value).
        dependant_value = get_dependant_value(component, financials, this_index, 'capex')
        # Update cost
        update_cost(component, financials, this_index, dependant_value, 'CAPEX/OPEX')


def update_emissions(component, emissions):
    """ Calculate fixed and operational emissions for this component.

    This function is calculating a fix and operational value for components
    where "fix_emissions" or "op_emissions" are dependant on certain values.
    The following list shows possible fitting methods. The fitting method is
    chosen by the "key" value given in the "emissions" dictionary:

    * "fix"      --> already the fix value, nothing has to be done
    * "spec"     --> cost value needs to be multiplied with the dependant value
    * "exp"      --> exponential cost fitting
    * "poly"     --> polynomial cost fitting
    * "free"     --> polynomial cost fitting with free choosable exponents

    If multiple keys are defined, the calculations are done sequentially in order.

     * "variable" --> definition of multiple "fix_emissions" or "op_emissions" structures:
    If the emission structure changes over the size of a specific value of the component, for example because of the
    effects of economics of scale, the special key "variable" can be used to define multiple "fix_emissions" or
    "op_emissions" dicts for different ranges of this value

    :param component: object of this component
    :type component:  component: :class:`~smooth.components.component.Component`
    :param emissions: emission object of this component
    :type emissions: fix_emissions or op_emissions dict
    """

    # Check if this emission dictionary is empty. If so, nothing has to be calculated.
    if not emissions:
        return

    # Check if 'variable' capex are beeing used, if so decide which capex is valid
    if emissions['key'] == 'variable':
        emissions = choose_valid_dict(component, emissions)

    # If the keys are not given as a list, they are transformed to one so they can be iterated.
    if type(emissions['key']) is not list:
        emissions['key'] = [emissions['key']]
        emissions['fitting_value'] = [emissions['fitting_value']]
        emissions['dependant_value'] = [emissions['dependant_value']]

    # Loop through each key.
    for this_index in range(len(emissions['key'])):
        # Get the dependant value (either given as a component value
        # or if dependant value key at this_index is cost 'fix_emissions' get
        # the previously calculated cost value).
        dependant_value = get_dependant_value(component, emissions, this_index, 'fix_emissions')
        # Update cost
        update_cost(component, emissions, this_index, dependant_value, 'Emissions')


def update_cost(component, fitting_dict, index, dependant_value, name):
    """Update cost of component.

    :param component: object of this component
    :type component: :class:`~smooth.components.component.Component`
    :param fitting_dict: usually financial or emission object of this component
    :type fitting_dict: dict
    :param index: current position in fitting_dict
    :type index: integer
    :param dependant_value: dependent attribute value of object
    :type dependant_value: number
    :param name: human readable representation of attribute to be updated,
        e.g. "CAPEX/OPEX" or "emissions"
    :type name: string
    :raises ValueError: on unknown fitting key
    """
    this_key = fitting_dict['key'][index]
    if this_key == 'fix':
        # Fixed costs do not have to be processed further.
        pass
    elif this_key == 'spec':
        fitting_dict['cost'] = get_spec(component, fitting_dict, index, dependant_value)
    elif this_key == 'exp':
        fitting_dict['cost'] = get_exp(component, fitting_dict, index, dependant_value)
    elif this_key == 'poly':
        fitting_dict['cost'] = get_poly(component, fitting_dict, index, dependant_value)
    elif this_key == 'free':
        fitting_dict['cost'] = get_free(component, fitting_dict, index, dependant_value)
    else:
        raise ValueError(
            '{} key "{}" not recognized. Please choose a valid key.'.format(name, this_key))


def get_spec(component, fitting_dict, index, dependant_value):
    """Case: The fitting value is multiplied with the dependant value to get the costs.

    :param component: object of this component
    :type component: :class:`~smooth.components.component.Component`
    :param fitting_dict: usually financial or emission object of this component
    :type fitting_dict: dict
    :param index: current position in fitting_dict
    :type index: integer
    :param dependant_value: dependent attribute value of object
    :type dependant_value: number
    :return: calculated costs using a fitting value
    :rtype: number
    """

    # Get the fitting value, which is the current cost if "cost" is chosen.
    if fitting_dict['fitting_value'][index] == 'cost':
        fitting_value = fitting_dict['cost']
    else:
        fitting_value = fitting_dict['fitting_value'][index]
    # Calculate the costs.
    cost = dependant_value * fitting_value

    # Return the costs.
    return cost


def get_exp(component, fitting_dict, index, dependant_value):
    """Case: An exponential fitting of the cost function is wanted.

    Here 3 variables are used in the following order::

        # for 2 fitting parameters
        fv_1*exp(fv_2)

        # for 3 fitting parameters
        fv_1 + fv_2*exp(fv_3*Parameter)

    :param component: object of this component
    :type component: :class:`~smooth.components.component.Component`
    :param fitting_dict: usually financial or emission object of this component
    :type fitting_dict: dict
    :param index: current position in fitting_dict
    :type index: integer
    :param dependant_value: dependent attribute value of object
    :type dependant_value: number
    :return: calculated costs using exponential fitting
    :rtype: number
    """

    # Get the fitting values.
    fv = fitting_dict['fitting_value'][index]

    if len(fv) == 2:
        # If only two fitting values are given, it is assumed that the constant value is 0.
        fv = [0, *fv]
    # Calculate the costs.
    cost = fv[0] + fv[1] * math.exp(fv[2] * dependant_value)

    # Return the costs.
    return cost


def get_poly(component, fitting_dict, index, dependant_value):
    """Case: An polynomial fitting of the cost function is wanted.

    In this case, an arbitrary number of fitting parameters can be given.
    They will be used in the following order: fv_1, fv_2, fv_3, ... fv_n.

    Function::

        fv_1 + fv_2*dependant_value + fv_3*dependant_value^2 + ... fv_n*dependant_value^(n-1)

    :param component: object of this component
    :type component: :class:`~smooth.components.component.Component`
    :param fitting_dict: usually financial or emission object of this component
    :type fitting_dict: dict
    :param index: current position in fitting_dict
    :type index: integer
    :param dependant_value: dependent attribute value of object
    :type dependant_value: number
    :return: calculated costs using polynomial fitting
    :rtype: number
    """

    # Get the fitting values.
    fv = fitting_dict['fitting_value'][index]
    # Get the number of fitting values [-].
    n_fv = len(fv)

    # In a loop, calculate the costs.
    cost = 0
    for i_fv in range(n_fv):
        if fv[i_fv] == 'cost':
            fv[i_fv] = fitting_dict['cost']
        cost += fv[i_fv] * dependant_value ** i_fv

    # Return the costs.
    return cost


def get_free(component, fitting_dict, index, dependant_value):
    """Case: A "free" fitting of the cost function is wanted.

    In this case, an arbitrary number of fitting parameters can be given.
    They will be used in the following order: fv_1, fv_2, fv_3, ... fv_n.

    Function::

        fv_1*dependant_value^fv_2 + fv_3*dependant_value^fv_4 + ... fv_(n-1)*dependant_value^fv_n

    :param component: object of this component
    :type component: :class:`~smooth.components.component.Component`
    :param fitting_dict: usually financial or emission object of this component
    :type fitting_dict: dict
    :param index: current position in fitting_dict
    :type index: integer
    :param dependant_value: dependent attribute value of object
    :type dependant_value: number
    :return: calculated costs using "free" fitting
    :rtype: number
    :raises ValueError: if number of fitting values is odd
    """

    # Get the fitting values.
    fv = fitting_dict['fitting_value'][index]
    # Get the number of fitting values [-].
    n_fv = len(fv)

    # The number of fitting values needs to be even, otherwise throw an error.
    if n_fv % 2 != 0:
        raise ValueError(
            'In component {}, the number of fitting values is {}, but it needs to be even!'
            .format(component['name'], n_fv))

    # Cost value
    cost = 0
    for i in range(int(n_fv/2)):
        cost += fv[i*2] * dependant_value**fv[i*2 + 1]

    # Return the costs.
    return cost


def get_dependant_value(component, fitting_dict, index, fixedCost):
    """Get an attribute of the component as the dependant value.

    :param component: object of this component
    :type component: :class:`~smooth.components.component.Component`
    :param fitting_dict: usually financial or emission object of this component
    :type fitting_dict: dict
    :param index: current position in fitting_dict
    :type index: integer
    :param fixedCost: key of fixed type in fitting_dict
    :type fixedCost: string
    :return: calculated costs using exponential fitting
    :rtype: number or None
    """

    if fitting_dict['key'][index] != 'fix':
        dependant_value = getattr(component, fitting_dict['dependant_value'][index], None)
    else:
        dependant_value = None

    if fitting_dict['dependant_value'][index] == fixedCost:
        # If the capex are chosen as the dependant value, the capex costs are meant.
        # Check if 'variable' capex are beeing used, if so decide which capex is valid
        if dependant_value['key'] == 'variable':
            dependant_value = choose_valid_dict(component, dependant_value)
        dependant_value = dependant_value['cost']

    return dependant_value
