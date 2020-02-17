from bokeh.plotting import figure, output_file, show
from bokeh.layouts import row
from bokeh.palettes import Spectral11
import pandas as pd
from bokeh.io import export_png


def plot_interactive_smooth_results(smooth_result):
    # Plots the results of a smooth run - the distinction between this function and the 'plot_results'
    # function is: 1) all figures are displayed at once, 2) the plots are more interactive e.g. legends can be hidden
    # Parameter:
    #  smooth_results: Smooth result file containing all components [list].

    # Creates empty dict which will later contain the busses that will be plotted.
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
                # Replaces shorthand component names in the results with the official names for those listed.
                if component_result.name == 'this_ely':
                    component_result.name = 'Elektrolyseur'
                elif component_result.name == 'this_pem_ely':
                    component_result.name = 'PEM-Elektrolyseur'
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
                    # If bus name didn't appear so far, add it to the list of busses.
                    busses_to_plot[this_bus] = dict()

                # Add the flow of this component to this bus.
                busses_to_plot[this_bus][component_result.name] = this_comp_flows[this_bus]

    # Creates empty dict which will contain the figures for each individual bus.
    figures = {}
    for this_bus in busses_to_plot:
        # Replaces shorthand bus names with the official names for those listed.
        if this_bus == 'bel':
            bus_label = 'Elektrische Energie'
            y_label = 'Energie in Wh'
        elif this_bus == 'bth':
            bus_label = 'Thermische Energie'
            y_label = 'Energie in Wh'
        elif this_bus == 'bh2_lp':
            bus_label = 'Wasserstoff-Fluss bei Niederdruck'
            y_label = 'Wasserstoff in kg'
        elif this_bus == 'bh2_mp':
            bus_label = 'Wasserstoff-Fluss bei Mitteldruck'
            y_label = 'Wasserstoff in kg'
        elif this_bus == 'bh2_hp':
            bus_label = 'Wasserstoff-Fluss bei Hochdruck'
            y_label = 'Wasserstoff in kg'
        elif this_bus == 'bch4':
            bus_label = 'Biomethan-Fluss'
            y_label = 'Biomethan in kg'

        # Creates a new figure for plotting for this bus.
        figures[this_bus] = figure(plot_width=800, plot_height=600, title=bus_label, x_axis_label='Stunden des Jahres',
                                   y_axis_label=y_label)
        # Creates a dataframe of all flows leaving/entering this bus.
        df = pd.DataFrame.from_dict(busses_to_plot[this_bus])
        # Detects how many different flows are leaving/entering this bus.
        num_lines = len(df.columns)
        # Assigns each flow a different colour from the chosen palette.
        my_palette = Spectral11[0:num_lines]

        # Creates a list of x values to represent the number of hours.
        xs = [df.index.values] * num_lines
        # Creates a list of the lists of flows for each bus
        ys = [df[component].values for component in df]

        for this_component, this_flow in busses_to_plot[this_bus].items():
            # Loops through the colour palette, the legend labels, the x lists (xs) and the y lists (ys).
            for (colours, legend_labels, x, y) in zip(my_palette, busses_to_plot[this_bus].keys(), xs, ys):
                my_plot = figures[this_bus].line(x, y, color=colours, legend_label=legend_labels)
            # Sets the legend in the top left corner of the figure.
            figures[this_bus].legend.location = "top_left"
            # Enables the legends to be seen or hidden.
            figures[this_bus].legend.click_policy = "hide"
    # Create a list of figures to later enable them to be displayed in a row.
    list_of_figures = []
    for this_bus in figures:
        list_of_figures.append(figures[this_bus])
    # Displays figures in a row (this can be changed to column).
    show(row(list_of_figures))
    # COMMENT: this could be made so that it is saved specifically for each results

    export_png(list_of_figures, filename="plot.png")