import csv


def save_important_parameters(optimization_results, result_file_name):
    # Saves the most important parameters from optimization results in a csv file
    # Parameter:
    # optimization_results: file containing all information about the optimization results

    if result_file_name.endswith('.pickle'):
        result_file_name = result_file_name[:-7]
    # create an empty csv file
    with open('important_params_' + str(result_file_name), 'w', newline='') as file:
        writer = csv.writer(file)
        headers = ['Component', 'Parameter', 'Value']
        writer.writerow(headers)
        for component in optimization_results.best_smooth_result:
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
            if component.flows.get('flow: from_grid-->bel') is not None:
                total_from_grid = sum(component.flows['flow: from_grid-->bel'])
                entry = [name, 'annual grid supply', total_from_grid]
                writer.writerow(entry)
            # looks through all components to check for h2 demand component,
            # and calculates the annual demand and the maximum hourly demand in
            # the year
            elif component.flows.get('flow: bh2_hp-->h2_demand') is not None:
                total_h2_demand = sum(component.flows['flow: bh2_hp-->h2_demand'])
                entry = [name, 'total demand (hydrogen)', total_h2_demand]
                writer.writerow(entry)
                maximum_flow = max(component.flows['flow: bh2_hp-->h2_demand'])
                entry = [name, 'maximum hourly demand', maximum_flow]
                writer.writerow(entry)
            # looks through all components to check for thermal demand
            # component, and calculates annual demand
            elif component.flows.get('flow: bth-->th_demand') is not None:
                total_h2_demand = sum(component.flows['flow: bth-->th_demand'])
                entry = [name, 'total demand (thermal)', total_h2_demand]
                writer.writerow(entry)
