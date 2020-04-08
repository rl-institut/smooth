from matplotlib import pyplot as plt
from smooth.framework.functions.functions import extract_flow_per_bus
from smooth.examples.example_plotting_dicts import comp_dict, bus_dict, y_dict


def plot_smooth_results(smooth_result, comp_label_dict=comp_dict, bus_dict=bus_dict, y_dict=y_dict):
    # Extract dict containing the busses that will be plotted.
    busses_to_plot = extract_flow_per_bus(smooth_result, comp_label_dict)

    # Plot each bus in a new window.
    for this_bus in busses_to_plot:
        print(this_bus)
        for this_component, this_flow in busses_to_plot[this_bus].items():
            plt.plot(this_flow, label=str(this_component))
        plt.legend()
        plt.xlabel('Stunden des Jahres')
        try:
            plt.title(bus_dict[this_bus])
            plt.ylabel(y_dict[this_bus])
        except:
            plt.title('bus: ' + this_bus)

        plt.show()
