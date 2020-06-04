import csv
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set()


def save_important_parameters(optimization_results, result_index, result_filename, comp_dict):
    """Saves the most important parameters from the optimization results in a csv file, and
    automatically generates pie plots containing the results of financial annuity shares,
    emission shares and electricity usage shares between components in the energy system.

    :param optimization_results: The file containing all information about the optimization results
    :type optimization_results: ?
    :param result_index: The index number that relates to the specific optimization result
    :type result_index: int
    :param result_filename: The result filename e.g. 'my_optimization_results.pickle'
    :type result_filename: pickle
    """

    if result_filename.endswith('.pickle'):
        result_file_name = result_filename[:-7]
    # create an empty csv file
    with open(str(result_filename + '_important_params'), 'w', newline='') as file:
        writer = csv.writer(file)
        headers = ['Component', 'Parameter', 'Value']
        writer.writerow(headers)

        # Lists used in pie plots
        component_names = []
        component_annuities = []
        component_emissions = []
        component_elec_use = []
        component_elec_use_names = []

        for component in optimization_results[result_index].smooth_result:
            name = component.name
            # looks through all components to find the maximum power attributes
            if hasattr(component, 'power_max'):
                entry = [name, 'maximum power', component.power_max]
                writer.writerow(entry)
            # looks through all components to find nominal value of e.g. energy
            # sources and multiplies this value by a reference value to obtain
            # the actual value (maximum power)
            elif hasattr(component, 'nominal_value') and hasattr(component, 'reference_value'):
                power_max = component.nominal_value * component.reference_value
                entry = [name, 'maximum power', power_max]
                writer.writerow(entry)
            # looks through all components to find storage capacity value
            elif hasattr(component, 'storage_capacity'):
                entry = [name, 'storage capacity', component.storage_capacity]
                writer.writerow(entry)

            # looks through all components to check for the supply component,
            # and calculates the annual power supply
            if component.flows.get(tuple('from_grid, bel')) is not None:
                total_from_grid = sum(component.flows[tuple('from_grid, bel')])
                entry = [name, 'annual grid supply', total_from_grid]
                writer.writerow(entry)
            # looks through all components to check for h2 demand component,
            # and calculates the annual demand and the maximum hourly demand in
            # the year
            elif component.flows.get(tuple('bh2_hp, h2_demand')) is not None:
                total_h2_demand = sum(component.flows[tuple('bh2_hp, h2_demand')])
                entry = [name, 'total demand (hydrogen)', total_h2_demand]
                writer.writerow(entry)
                maximum_flow = max(component.flows[tuple('bh2_hp, h2_demand')])
                entry = [name, 'maximum hourly demand', maximum_flow]
                writer.writerow(entry)
            # looks through all components to check for thermal demand
            # component, and calculates annual demand
            elif component.flows.get(tuple('bth, th_demand')) is not None:
                total_h2_demand = sum(component.flows[tuple('bth, th_demand')])
                entry = [name, 'total demand (thermal)', total_h2_demand]
                writer.writerow(entry)

            this_annuity = component.results['annuity_total']
            this_emission = component.results['annual_total_emissions']
            if name in comp_dict.keys():
                name = comp_dict[name]

            for this_tuple in component.flows:
                if this_tuple[0] == 'bel':
                    total_elec_use = sum(component.flows[tuple(this_tuple)])
                    component_elec_use.append(total_elec_use)
                    component_elec_use_names.append(name)

            if component.component != 'gate':
                component_names.append(name)
            component_annuities.append(this_annuity)
            component_emissions.append(this_emission)

    # Sets the colour palette for the pie plots
    palette = sns.color_palette()

    # ---------------- FINANCIAL ANNUITY PIE PLOT ---------------
    component_names = np.char.array(component_names)
    component_annuities = np.array(component_annuities)
    annuity_shares = 100.*component_annuities/component_annuities.sum()

    patches_1, texts_1 = plt.pie(component_annuities, startangle=90, colors=palette)
    labels = ['{0}: {1:1.2f} %'.format(i, j) for i, j in zip(component_names, annuity_shares)]
    plt.legend(patches_1, labels, loc='best', bbox_to_anchor=(-0.1, 1.),
               fontsize=8)
    plt.title('Percentage share of total annuity')
    plt.tight_layout()
    plt.show()
    plt.savefig(str(result_filename) + '_annuity_breakdown.png')

    # ---------------- EMISSION ANNUITY PIE PLOT ---------------
    component_emissions = np.array(component_emissions)
    emission_shares = 100.*component_emissions/component_emissions.sum()

    patches_2, texts_2 = plt.pie(component_emissions, startangle=90, colors=palette)
    labels = ['{0}: {1:1.2f} %'.format(i, j) for i, j in zip(component_names, emission_shares)]
    plt.legend(patches_2, labels, loc='best', bbox_to_anchor=(-0.1, 1.),
               fontsize=8)
    plt.title('Percentage share of total emissions')
    plt.tight_layout()
    plt.show()
    plt.savefig(str(result_filename) + '_emissions_breakdown.png')

    # ---------------- ELECTRICITY USE PIE PLOT ---------------
    component_elec_use_names = np.char.array(component_elec_use_names)
    component_elec_use = np.array(component_elec_use)
    elec_use_shares = 100.*component_elec_use/component_elec_use.sum()

    patches_3, texts_3 = plt.pie(component_elec_use, startangle=90, colors=palette)
    labels = ['{0}: {1:1.2f} %'.format(i, j)
              for i, j in zip(component_elec_use_names, elec_use_shares)]
    plt.legend(patches_3, labels, loc='best', bbox_to_anchor=(-0.1, 1.),
               fontsize=8)
    plt.title('Percentage share of electricity use')
    plt.tight_layout()
    plt.show()
    plt.savefig(str(result_filename) + '_electricity_use_breakdown.png')

    return
