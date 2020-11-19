from bokeh.plotting import figure, show
from bokeh.layouts import row
from bokeh.palettes import Spectral11
import pandas as pd
from bokeh.io import export_png
from smooth.framework.functions.functions import extract_flow_per_bus
from smooth.examples.example_plotting_dicts import comp_dict_german, bus_dict_german, y_dict_german


def plot_interactive_smooth_results(
        smooth_result,
        comp_label_dict=comp_dict_german,
        bus_dict=bus_dict_german,
        y_dict=y_dict_german):
    # Plots the results of a smooth run - the distinction between this function
    # and the 'plot_results' function is:
    #    1) all figures are displayed at once,
    #    2) the plots are more interactive e.g. legends can be hidden
    #
    # Parameter:
    #  smooth_results: Smooth result file containing all components [list].

    # Extract dict containing the busses that will be plotted.
    busses_to_plot = extract_flow_per_bus(smooth_result, comp_label_dict)

    # Creates empty dict which will contain the figures for each individual bus.
    figures = {}
    for this_bus in busses_to_plot:
        # Replaces shorthand bus names with the official names for those listed.
        try:
            bus_label = bus_dict[this_bus]
            y_label = y_dict[this_bus]
        except KeyError:
            bus_label = 'bus: ' + this_bus
            y_label = ''

        # Creates a new figure for plotting for this bus.
        figures[this_bus] = figure(
            plot_width=800,
            plot_height=600,
            title=bus_label,
            x_axis_label='Stunden des Jahres',
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
            # Loops through the colour palette, the legend labels,
            # the x lists (xs) and the y lists (ys).
            labels = busses_to_plot[this_bus].keys()
            for (colours, legend_label, x, y) in zip(my_palette, labels, xs, ys):
                figures[this_bus].line(x, y, color=colours, legend_label=legend_label)
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
