from matplotlib import pyplot as plt
from smooth.framework.functions.functions import extract_flow_per_bus


def plot_smooth_results(smooth_result, name_label_dict=dict()):
    # Extract dict containing the busses that will be plotted.
    busses_to_plot = extract_flow_per_bus(smooth_result, name_label_dict)

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
