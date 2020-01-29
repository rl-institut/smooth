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
                # Identify the number of trailing None values in case the optimization stopped before termination
                nb_trailing_none = len(component_flows[flow])
                for flow_val in component_flows[flow]:
                    if flow_val is not None:
                        nb_trailing_none -= 1
                    else:
                        break
                if this_flow_name_split[0] == component_result.name:
                    # Case: Component flows into bus.
                    bus = this_flow_name_split[1]
                    # Check if this component already has a flow with this bus.
                    if bus in this_comp_flows:
                        updated_bus_list = []
                        for i_val in range(len(this_comp_flows[bus]) - nb_trailing_none):
                            # Get the summed up value.
                            this_val = this_comp_flows[bus][i_val] + component_flows[flow][i_val]
                            updated_bus_list.append(this_val)
                        # Override the old bus list with the updated one.
                        this_comp_flows[bus] = updated_bus_list
                    else:
                        # Case: Component has no flow with this bus yet.
                        this_comp_flows[bus] = component_flows[flow][:-nb_trailing_none]

                else:
                    # Case: Component takes from bus.
                    bus = this_flow_name_split[0]
                    # Check if this component already has a flow with this bus.
                    if bus in this_comp_flows:
                        updated_bus_list = []
                        for i_val in range(len(this_comp_flows[bus]) - nb_trailing_none):
                            # Get the summed up value.
                            this_val = this_comp_flows[bus][i_val] - component_flows[flow][i_val]
                            updated_bus_list.append(this_val)
                        # Override the old bus list with the updated one.
                        this_comp_flows[bus] = updated_bus_list
                    else:
                        # Case: Component has no flow with this bus yet.
                        this_comp_flows[bus] = [-this_val for this_val in component_flows[flow][:-nb_trailing_none]]

            for this_bus in this_comp_flows:
                if this_bus not in busses_to_plot:
                    # If bus name didnt't appear so far, add it to the list of busses.
                    busses_to_plot[this_bus] = dict()

                # Add the flow of this component to this bus.
                busses_to_plot[this_bus][component_result.name] = this_comp_flows[this_bus]

    if(nb_trailing_none > 0):
        print('The flow sequences have {} trailing None values. Did the optimization terminate?'.format(nb_trailing_none))

    # Plot each bus in a new window.
    for this_bus in busses_to_plot:

        for this_component, this_flow in busses_to_plot[this_bus].items():
            plt.plot(this_flow, label=str(this_component))
        plt.legend()
        plt.title('bus: ' + this_bus)
        plt.show()
