from matplotlib import pyplot as plt


def plot_smooth_results_mpc(smooth_result):

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
                elif component_result.name == 'solar_output':
                    component_result.name = 'PV-Anlage'
                elif component_result.name == 'wind_output':
                   component_result.name = 'WE-Anlage'
                elif component_result.name == 'th_demand':
                    component_result.name = 'Heizbedarf'
                elif component_result.name == 'h2_demand':
                    component_result.name = 'Wasserstoffbedarf'
                elif component_result.name == 'h2_compressor':
                    component_result.name = 'Wasserstoffkompressor'
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

                if this_bus not in busses_to_plot:
                    # If bus name didnt't appear so far, add it to the list of busses.
                    busses_to_plot[this_bus] = dict()

                # Add the flow of this component to this bus.
                busses_to_plot[this_bus][component_result.name] = this_comp_flows[this_bus]

    # Plot the system inputs and system outputs of mpc
    # system inputs:
    plt.figure(1)
    plt.subplot(221)
    plt.plot(busses_to_plot['bel']['Elektrolyseur'], label='Elektrolyseur')
    plt.legend()
    plt.grid()
    plt.ylabel('Energie in Wh')
    plt.subplot(222)
    plt.plot(busses_to_plot['bh2_lp']['Brennstoffzelle'], label='Brennstoffzelle')
    plt.ylabel('Wasserstoff in kg')
    plt.legend()
    plt.grid()
    plt.subplot(223)
    plt.plot(busses_to_plot['bch4']['Biogas-BHKW'], label='Biogas-BHKW')
    plt.xlabel('Stunden des Jahres')
    plt.ylabel('Biomethan in kg')
    plt.legend()
    plt.grid()
    plt.subplot(224)
    plt.plot(busses_to_plot['bh2_lp']['h2_compressor_mp'], label='Kompressor lp')
    plt.xlabel('Stunden des Jahres')
    plt.ylabel('Wasserstoff in kg')
    plt.legend()
    plt.grid()
    plt.show()
    # system outputs
    plt.figure(2)
    plt.subplot(221)
    plt.plot(busses_to_plot['bel']['Stromeinspeisung'], label='Stromeinspeisung')
    # plt.plot(busses_to_plot['bel']['Strombezug'], label='Strombezug')
    plt.legend()
    plt.grid()
    # plt.show()
    plt.ylabel('Energie in Wh')
    plt.subplot(222)
    plt.plot(busses_to_plot['bh2_lp']['sink_h2_lp'], label='Wasserstoffeinspeisung lp')
    plt.ylabel('Wasserstoff in kg')
    plt.legend()
    plt.grid()
    plt.subplot(223)
    plt.plot(busses_to_plot['bh2_hp']['sink_h2_hp'], label='Wasserstoffeinspeisung hp')
    plt.xlabel('Stunden des Jahres')
    plt.ylabel('Wasserstoff in kg')
    plt.legend()
    plt.grid()
    plt.subplot(224)
    plt.plot(busses_to_plot['bth']['sink_th'], label='Wärmeeinspeisung')
    plt.xlabel('Stunden des Jahres')
    plt.ylabel('Energie in Wh')
    plt.legend()
    plt.grid()
    plt.show()

