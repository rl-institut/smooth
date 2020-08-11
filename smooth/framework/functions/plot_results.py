from matplotlib import pyplot as plt
from smooth.framework.simulation_parameters import SimulationParameters
from smooth.framework.functions.functions import extract_flow_per_bus
from smooth.examples.example_plotting_dicts import comp_dict_german, bus_dict_german, y_dict_german


def plot_smooth_results(smooth_result, comp_label_dict=comp_dict_german,
                        bus_dict=bus_dict_german, y_dict=y_dict_german):
    # Extract dict containing the busses that will be plotted.
    busses_to_plot = extract_flow_per_bus(smooth_result, comp_label_dict)

    # get first sim_params from smooth_result component for interval_time
    sim_params = next(
        (comp.sim_params for comp in smooth_result if hasattr(comp, 'sim_params')),
        SimulationParameters({})  # default values
    )

    # Plot each bus in a new window.
    for this_bus in busses_to_plot:
        for this_component, this_flow in busses_to_plot[this_bus].items():
            # get time axis (in hours, interval_time is in minutes)
            timeseries = [sim_params.interval_time/60 * t for t in range(len(this_flow))]
            plt.plot(timeseries, this_flow, label=str(this_component))
        plt.legend()
        plt.xlabel('Stunden des Jahres')
        try:
            plt.title(bus_dict[this_bus])
            plt.ylabel(y_dict[this_bus])
        except KeyError:
            plt.title('bus: ' + this_bus)

        plt.show()
