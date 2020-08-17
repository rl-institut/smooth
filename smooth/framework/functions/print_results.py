def print_smooth_results(smooth_results):
    """Print the financial results of a smooth run.

    :param smooth_results: result from run_smooth containing all components
    :type smooth_results: list of :class:`~smooth.components.component.Component`
    """

    # Calculate the sum of all total annuities [EUR/a] and annual emissions [kg/a].
    sum_of_tot_annuity = 0
    sum_of_tot_ann_emission = 0

    print("\n++++++++")
    print('RESULTS:')
    print("++++++++\n")
    print('{:20s} {:20s} {:20s} {:20s} {:20s} {:20s} {:20s} {:20s}'.format(
        'component name', 'annutiy capex', 'annuity opex', 'annuity var. cost', 'annuity total',
        'annual fix GGE', 'annual var. GGE', 'annual total GGE'
    ))

    for this_comp in smooth_results:
        # Print the annuity costs for each component.
        print('{:20s} {:<20d} {:<20d} {:<20d} {:<20d} {:<20d} {:<20d} {:<20d}'.format(
            this_comp.name,
            int(this_comp.results['annuity_capex']),
            int(this_comp.results['annuity_opex']),
            int(this_comp.results['annuity_variable_costs']),
            int(this_comp.results['annuity_total']),
            int(this_comp.results['annual_fix_emissions']),
            int(this_comp.results['annual_variable_emissions']),
            int(this_comp.results['annual_total_emissions'])
        ))
        # print('Comp: {}: flow: {}'.format(this_comp.name, this_comp.flows))
        # print('Comp: {}: states: {}'.format(this_comp.name, this_comp.states))
        # print('Comp: {}: results: {}'.format(this_comp.name, this_comp.results))

        sum_of_tot_annuity += this_comp.results['annuity_total']
        sum_of_tot_ann_emission += this_comp.results['annual_total_emissions']

    print('\nSum of total annuity is {} EUR/a'.format(int(sum_of_tot_annuity)))
    print('\nSum of total annual emission is {} kg/a'.format(int(sum_of_tot_ann_emission)))
