import math

def print_smooth_results(smooth_results):
    # Print the financial results of a smooth run.
    # Parameter:
    #  smooth_results: Smooth result file containing all components [list].

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
            this_comp.name, math.floor(this_comp.results['annuity_capex']),
            math.floor(this_comp.results['annuity_opex']),
            math.floor(this_comp.results['annuity_variable_costs']),
            math.floor(this_comp.results['annuity_total']),
            math.floor(this_comp.results['annual_fix_emissions']),
            math.floor(this_comp.results['annual_variable_emissions']),
            math.floor(this_comp.results['annual_total_emissions'])
        ))
        # print('Comp: {}: flow: {}'.format(this_comp.name, this_comp.flows))
        sum_of_tot_annuity += this_comp.results['annuity_total']
        sum_of_tot_ann_emission += this_comp.results['annual_total_emissions']




    print('\nSum of total annuity is {} EUR/a'.format(math.floor(sum_of_tot_annuity)))
    print('\nSum of total annual emission is {} kg/a'.format(math.floor(sum_of_tot_ann_emission)))
