

def update_annuities(component):
    # Convert the CAPEX and variable costs to annuities.
    # Parameter:
    #  component: object of one component.

    # First calculate the annuities for the CAPEX.
    capex = component.capex
    # When the capex dict is empty, the annuity is zero, otherwise it has to be calculated.
    if not capex:
        # There are no CAPEX, so the annuity is 0 [EUR/a].
        capex_annuity = 0
    else:
        # Interest rate [-].
        interest_rate = component.sim_params.interest_rate
        # Calculate the capital recovery factor [-].
        capital_recovery_factor = (interest_rate * (1 + interest_rate)**component.life_time) / \
                                  (((1 + interest_rate)**component.life_time) - 1)
        # Calculate the annuity of the CAPEX [EUR/a].
        capex_annuity = capex['cost'] * capital_recovery_factor

    # Check if OPEX were calculated, if so they are directly in annuity format.
    if not component.opex:
        opex = 0
    else:
        opex = component.opex['cost']

    # Then calculate the annuity of the variable costs. This is only needed if the simulation did not take a whole year.
    # In case it was a different time period, the costs per year have to be estimated by assuming the variable costs of
    # the simulation period can be used as an average over the simulation time.

    # Calculate the ratio of simulation time to one year (sim_time_span is in minutes) [-].
    time_ratio = component.sim_params.sim_time_span / (365 * 24 * 60)
    # Get the total amount of variable costs [EUR].
    variable_cost_tot = sum(component.results['variable_costs'])
    # Get the annuity of the variable cost [EUR/a].
    variable_cost_annuity = variable_cost_tot / time_ratio

    # Save the cost results.
    component.results['annuity_capex'] = capex_annuity
    component.results['annuity_opex'] = opex
    component.results['annuity_variable_costs'] = variable_cost_annuity
    component.results['annuity_total'] = capex_annuity + opex + variable_cost_annuity




