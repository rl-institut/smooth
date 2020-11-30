from smooth.framework.functions.functions import choose_valid_dict


def update_annuities(component):
    """Compute the annual CAPEX, variable costs and emissions.

    Annuities are written into the *results* dictionary of the component.

    :param component: object of this component
    :type component: :class:`~smooth.components.component.Component`
    """

    # First calculate the annuities for the CAPEX in EUR/a.
    # If there are no CAPEX (dict is empty), the annuity is 0 EUR/a,
    # otherwise it is a product of capex and capital recovery factor [-].
    capex_annuity = calc_annuity(component, component.capex)
    # Check if OPEX were calculated, if so they are directly in annuity format.
    if not component.opex:
        opex = 0
    else:
        # Check if 'variable' opex are beeing used, if so decide which opex is valid
        if component.opex['key'] == 'variable':
            component.opex = choose_valid_dict(component, component.opex)
        opex = component.opex['cost']

    # Calculate the annual emissions for the installation in kg/a.
    # If the emissions are not given (dict is empty), the annual emissions are 0 kg/a,
    # otherwise it is a fraction of fix_emissions divided by the component's life-time in years.
    fix_emissions_annual = calc_annual_emissions(component, component.fix_emissions)
    # Check if operational emissions were calculated, if so they are directly in annual format.
    if not component.op_emissions:
        op_emissions = 0
    else:
        # Check if 'variable' op_emissions are being used, if so decide which
        # op_emissions are valid
        if component.op_emissions['key'] == 'variable':
            component.op_emissions = choose_valid_dict(component, component.op_emissions)
        op_emissions = component.op_emissions['cost']

    # Then calculate the annuity of the variable costs. This is only needed if
    # the simulation did not take a whole year. In case it was a different time
    # period, the costs per year have to be estimated by assuming the variable
    # costs of the simulation period can be used as an average over the
    # simulation time.

    # Calculate the ratio of simulation time to one year (sim_time_span is in minutes) [-].
    time_ratio = component.sim_params.sim_time_span / (365 * 24 * 60)
    # Get the total amount of variable costs [EUR].
    variable_cost_tot = sum(component.results['variable_costs'])
    # Get the annuity of the variable cost [EUR/a].
    variable_cost_annuity = variable_cost_tot / time_ratio

    # Get the total amount of variable emissions [kg].
    variable_emissions_tot = sum(component.results['variable_emissions'])
    # Get the annual emissions out of the variable emissions [kg/a].
    variable_emissions_annual = variable_emissions_tot / time_ratio

    # Save the cost results.
    component.results['annuity_capex'] = capex_annuity
    component.results['annuity_opex'] = opex
    component.results['annuity_variable_costs'] = variable_cost_annuity
    component.results['annuity_total'] = capex_annuity + opex + variable_cost_annuity

    component.results['annual_fix_emissions'] = fix_emissions_annual
    component.results['annual_op_emissions'] = op_emissions
    component.results['annual_variable_emissions'] = variable_emissions_annual
    component.results['annual_total_emissions'] = fix_emissions_annual + \
        op_emissions + variable_emissions_annual


def calc_annuity(component, target):
    """Calculate annuity

    :param component: object of this component
    :type component: :class:`~smooth.components.component.Component`
    :param target: dictionary with *cost* key, e.g. component.capex
    :type target: dict
    :return: annuity of target [EUR/a]
    :rtype: number
    """

    # When the target dict is empty, the annuity is zero, otherwise it has to be calculated.
    if not target:
        # There are no target entries, so the annuity is 0 in [target]/a.
        target_annuity = 0
    elif component.life_time == 0:
        # no lifetime in component: no annuity (avoid div0)
        target_annuity = 0
    else:
        # Interest rate [-].
        interest_rate = component.sim_params.interest_rate
        # Calculate the capital recovery factor [-].
        cap_nominator = interest_rate * (1 + interest_rate) ** component.life_time
        cap_denominator = ((1 + interest_rate) ** component.life_time) - 1
        capital_recovery_factor = cap_nominator / cap_denominator
        # Calculate the annuity of the target in [target]/a.

        # Check if 'variable' capex are being used, if so decide which capex is valid
        if target['key'] == 'variable':
            target = choose_valid_dict(component, target)
        target_annuity = target['cost'] * capital_recovery_factor

    return target_annuity


def calc_annual_emissions(component, target):
    """Calculate annual emissions.

    :param component: object of this component
    :type component: :class:`~smooth.components.component.Component`
    :param target: dictionary with *cost* key, e.g. component.fix_emissions
    :type target: dict
    :return: annual emissions of target [kg/a]
    :rtype: number
    """
    # When the target dict is empty, the annuity is zero, otherwise it has to be calculated.
    if not target:
        # There are no target entries, so the annuity is 0 in [target]/a.
        target_annuity = 0
    elif component.life_time == 0:
        # no lifetime in component: no annuity (avoid div0)
        target_annuity = 0
    else:

        if target['key'] == 'variable':
            target = choose_valid_dict(component, target)
        # Calculate the annuity of the target in [target]/a.
        target_annuity = target['cost'] / component.life_time

    return target_annuity


def update_external_annuities(component):
    """Convert the CAPEX to annuities

    Annuities are written into the *results* dictionary of the component.

    :param component: object of this component
    :type component: :class:`~smooth.components.component.Component`
    """

    # TODO: MAYBE CHANGE THE NAME?

    # First calculate the annuities for the CAPEX in EUR/a.
    # If there are no CAPEX (dict is empty), the annuity is 0 EUR/a,
    # otherwise it is a product of capex and capital recovery factor [-].
    capex_annuity = calc_annuity(component, component.capex)
    # Check if OPEX were calculated, if so they are directly in annuity format.
    if not component.opex:
        opex = 0
    else:
        opex = component.opex['cost']

        # Save the cost results.
    component.results['annuity_capex'] = capex_annuity
    component.results['annuity_opex'] = opex
    component.results['annuity_total'] = capex_annuity + opex

    # Calculate the annual emissions for the installation in kg/a.
    # If the emissions are not given (dict is empty), the annual emissions are 0 kg/a,
    # otherwise it is a fraction of fix_emissions divided by the component's life-time in years.
    fix_emissions_annual = calc_annual_emissions(component, component.fix_emissions)
    # Check if operational emissions were calculated, if so they are directly in annual format.
    if not component.op_emissions:
        op_emissions = 0
    else:
        op_emissions = component.op_emissions['cost']

    component.results['annual_fix_emissions'] = fix_emissions_annual
    component.results['annual_op_emissions'] = op_emissions
    component.results['annual_total_emissions'] = fix_emissions_annual + op_emissions
