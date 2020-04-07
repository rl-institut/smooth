from matplotlib import pyplot as plt


def plot_smooth_results(smooth_result):

    busses_to_plot = dict()

    for component_result in smooth_result:
        if hasattr(component_result, 'flows'):
            # Track the flows of this component.
            this_comp_flows = dict()
            component_flows = component_result.flows
            for flow in component_flows:
                # Get rid of "'flow: ".
                this_flow_name = flow[6:]
                this_flow_name_split = this_flow_name.split('-->')
                # check if it's a chp component which consists of two oemof models
                # if so get rid of the ending '_electric' or '_thermal'
                if this_flow_name_split[0][-9:] == '_electric':
                    this_flow_name_split[0] = this_flow_name_split[0][:-9]
                elif this_flow_name_split[0][-8:] == '_thermal':
                    this_flow_name_split[0] = this_flow_name_split[0][:-8]
                if this_flow_name_split[0] == component_result.name:
                    # Case: Component flows into bus.
                    bus = this_flow_name_split[1]
                    # Check if this component already has a flow with this bus.
                    if bus in this_comp_flows:
                        updated_bus_list = []
                        for i_val in range(len(this_comp_flows[bus])):
                            # Get the summed up value.
                            this_val = this_comp_flows[bus][i_val] + component_flows[flow][i_val]
                            updated_bus_list.append(this_val)
                        # Override the old bus list with the updated one.
                        this_comp_flows[bus] = updated_bus_list
                    else:
                        # Case: Component has no flow with this bus yet.
                        this_comp_flows[bus] = component_flows[flow]

                else:
                    # Case: Component takes from bus.
                    bus = this_flow_name_split[0]
                    # Check if this component already has a flow with this bus.
                    if bus in this_comp_flows:
                        updated_bus_list = []
                        for i_val in range(len(this_comp_flows[bus])):
                            # Get the summed up value.
                            this_val = this_comp_flows[bus][i_val] - component_flows[flow][i_val]
                            updated_bus_list.append(this_val)
                        # Override the old bus list with the updated one.
                        this_comp_flows[bus] = updated_bus_list
                    else:
                        # Case: Component has no flow with this bus yet.
                        this_comp_flows[bus] = [-this_val for this_val in component_flows[flow]]

            for this_bus in this_comp_flows:
                if component_result.name == 'this_ely':
                    component_result.name = 'Elektrolyseur'
                elif component_result.name == 'pv_output':
                    component_result.name = 'PV-Anlage'
                elif component_result.name == 'wind_output':
                    component_result.name = 'WE-Anlage'
                elif component_result.name == 'th_demand':
                    component_result.name = 'Heizbedarf'
                elif component_result.name == 'h2_demand':
                    component_result.name = 'Wasserstoffbedarf'
                elif component_result.name == 'h2_compressor':
                    component_result.name = 'Wasserstoffkompressor (higher pressure)'
                elif component_result.name == 'from_grid':
                    component_result.name = 'Strombezug'
                elif component_result.name == 'to_grid':
                    component_result.name = 'Stromeinspeisung'
                elif component_result.name == 'h2_storage':
                    component_result.name = 'Wasserstoffspeicher'
                elif component_result.name == 'fuel_cell_chp':
                    component_result.name = 'Brennstoffzelle'
                elif component_result.name == 'CHP_Methane':
                    component_result.name = 'Biogas-BHKW'
                elif component_result.name == 'ch4_grid':
                    component_result.name = 'Biogas-Zufuhr'
                elif component_result.name == 'h2_compressor_from_ely':
                    component_result.name = 'Wasserstoffkompressor (lower pressure)'
                elif component_result.name == 'dummy_2':
                    component_result.name = 'Gebrauchte PV-Elektrizität'
                elif component_result.name == 'dummy_1':
                    component_result.name = 'Gebrauchte Wind-Elektrizität'
                elif component_result.name == 'pv_to_grid':
                    component_result.name = 'Überschüssige PV-Elektrizität'
                elif component_result.name == 'wind_to_grid':
                    component_result.name = 'Überschüssige Wind-Elektrizität'

                if this_bus not in busses_to_plot:
                    # If bus name didnt't appear so far, add it to the list of busses.
                    busses_to_plot[this_bus] = dict()

                # Add the flow of this component to this bus.
                busses_to_plot[this_bus][component_result.name] = this_comp_flows[this_bus]

    busses_to_plot['bel']['Elektrolyseur']
    # Plot each bus in a new window.
    for this_bus in busses_to_plot:

        for this_component, this_flow in busses_to_plot[this_bus].items():
            plt.plot(this_flow, label=str(this_component))
        plt.legend()
        plt.xlabel('Stunden des Jahres')
        if this_bus == 'bel':
            plt.title('Elektrische Energie')
            plt.ylabel('Energie in Wh')
        elif this_bus == 'bel_wind':
            plt.title('Wind Energie')
            plt.ylabel('Energie in WH')
        elif this_bus == 'bel_pv':
            plt.title('PV Energie')
            plt.ylabel('Energie in WH')
        elif this_bus == 'bth':
            plt.title('Thermische Energie')
            plt.ylabel('Energie in Wh')
        elif this_bus == 'bh2_lp':
            plt.title('Wasserstoff-Fluss bei Niederdruck')
            plt.ylabel('Wasserstoff in kg')
        elif this_bus == 'bh2_mp':
            plt.title('Wasserstoff-Fluss bei Mitteldruck')
            plt.ylabel('Wasserstoff in kg')
        elif this_bus == 'bh2_hp':
            plt.title('Wasserstoff-Fluss bei Hochdruck')
            plt.ylabel('Wasserstoff in kg')
        elif this_bus == 'bch4':
            plt.title('Biomethan-Fluss')
            plt.ylabel('Biomethan in kg')
        else:
            plt.title('bus: ' + this_bus)
        plt.show()
