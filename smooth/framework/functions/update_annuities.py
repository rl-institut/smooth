


def update_annuities(component):

    # First calculate the annuities for the CAPEX.
    capex = component.capex
    # When the capex dict is empty, the annuity is zero, otherwise it has to be calculated.
    if not capex:
        # There are no CAPEX, so the annuity is 0 [EUR/a].
        capex_annuity = 0
    else:
        # Calculate the capital recovery factor [-].
        capital_recovery_factor = (component.interest_rate * (1 + component.interest_rate)**component.life_time) / \
                        (((1 + component.interest_rate)**component.life_time) - 1)
        # Calculate the annuity of the CAPEX [EUR/a].
        capex_annuity = capex['cost'] * capital_recovery_factor

    # Then calculate the annuity of the variable costs. This is only needed if the simulation did not take a whole year.
    # In case it was a different time period, the costs per year have to be estimated by assuming the variable costs of
    # the simulation period can be used as an average over the simulation time.

    # Calculate the ratio of simulation time to one year [-].
    time_ratio = 1


