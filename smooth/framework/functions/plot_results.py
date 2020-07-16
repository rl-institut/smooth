from matplotlib import pyplot as plt
from smooth.framework.functions.functions import extract_flow_per_bus
from smooth.examples.example_plotting_dicts import comp_dict_german, bus_dict_german, y_dict_german
import numpy as np


def plot_smooth_results(smooth_result, comp_label_dict=comp_dict_german,
                        bus_dict=bus_dict_german, y_dict=y_dict_german):
    # Extract dict containing the busses that will be plotted.
    busses_to_plot = extract_flow_per_bus(smooth_result, comp_label_dict)

    # Plot each bus in a new window.
    for this_bus in busses_to_plot:
        for this_component, this_flow in busses_to_plot[this_bus].items():
            plt.plot(this_flow, label=str(this_component))
        plt.legend()
        if smooth_result[0].sim_params.interval_time == 60:
            plt.xlabel('Stunden')
        elif smooth_result[0].sim_params.interval_time == 1:
            plt.xlabel('Minuten')
        else:
            plt.xlabel('Zeitschritt (≙' + str(smooth_result[0].sim_params.interval_time) + ' min)')

        try:
            plt.title(bus_dict[this_bus])
            plt.ylabel(y_dict[this_bus])
        except KeyError:
            plt.title('bus: ' + this_bus)
            
        plt.grid()

        locs, labels = plt.xticks()
        locs_new = np.arange(0, len(this_flow)+1, np.floor(abs(locs[0])))
        plt.xticks(locs_new)
        plt.show()
