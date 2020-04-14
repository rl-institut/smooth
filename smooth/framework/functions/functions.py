import os
import importlib
import pandas as pd
import re


def read_data_file(path, filename, csv_separator, column_title):
    # Function to read the input data files.
    # Parameters:
    #  path = path where the csv file is located [string].
    #  filename = name of csv file [string].
    file_path = os.path.join(path, filename)
    # create specific string for chosen data type
    data = pd.read_csv(file_path, sep=csv_separator, usecols=[column_title])
    return data


def get_date_time_index(start_date, n_intervals, step_size):
    # Function defining the parameters for perfect/myopic foresight:
    # Parameters:
    #  start_date: the first evaluated time period (e.g. '1/1/2019') [string].
    #  n_intervals: number of times the 'for' loop should run [-].
    #  step_size: Size of one time step [min].
    date_time_index = pd.date_range(start_date, periods=n_intervals, freq='{}min'.format(step_size))
    return date_time_index


def interval_time_index(date_time_index, i_interval):
    # Function to divide the set date time index into hourly intervals.
    # Parameters:
    #  date_time_index: chosen date range for the model
    #  this_time_index: the time at each 'for' loop
    this_time_index = date_time_index[i_interval: (i_interval + 1)]
    return this_time_index


def get_sim_time_span(n_interval, step_size):
    # Calculate the time span of the simulation.
    # Parameters:
    #  n_interval: number of intervals [-].
    #  step_size: Size of one time step [min].

    # Return the time delta in minutes [min].
    return n_interval * step_size


def create_component_obj(model, sim_params):
    # CREATE COMPONENT OBJECTS
    components = []
    for name, this_comp in model['components'].items():
        # Add simulation parameters to the components so they can be used
        this_comp['sim_params'] = sim_params
        # assign unique name
        this_comp['name'] = name
        # load the component class.
        this_comp_type = this_comp['component']
        # Component type should consist of lower case letters, numbers and underscores
        if re.fullmatch(r'[a-z0-9_]+', this_comp_type) is None:
            raise ValueError('Invalid component type name "{}". '\
                'Only lower case letters, numbers and underscores are allowed.'.format(this_comp_type))
        # Import the module of the component.
        this_comp_module = importlib.import_module('smooth.components.component_' + this_comp_type)
        # Convert component type from snake_case to CamelCase to get class name
        class_name = ''.join(x.capitalize() for x in this_comp_type.split('_'))
        # Load the class (which by convention has a name with a capital first letter and camel case).
        this_comp_class = getattr(this_comp_module, class_name)
        # Initialize the component.
        this_comp_obj = this_comp_class(this_comp)
        # Check if this component is valid.
        this_comp_obj.check_validity()
        # Add this component to the list containing all components.
        components.append(this_comp_obj)

    return components


def cut_suffix(str, suffix):
    # Cuts off the 'suffix' from 'str' if it ends with it
    # str: String from which suffix will be cut off
    # suffix: String, that is removed
    if str.endswith(suffix):
        str = str[:-len(suffix)]

    return str


def extract_flow_per_bus(smooth_result, name_label_dict):
    """
    Extract dict containing the busses that will be plotted.
    """
    # Creates empty dict which will later contain the busses that will be plotted.
    busses_to_plot = dict()
    nb_trailing_none = 0

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
                nb_intervals = len(component_flows[flow])
                nb_trailing_none = nb_intervals
                for flow_val in component_flows[flow]:
                    if flow_val is not None:
                        nb_trailing_none -= 1
                    else:
                        break
                # check if it's a chp component which consists of two oemof models
                # if so get rid of the ending '_electric' or '_thermal'
                this_flow_name_split[0] = cut_suffix(this_flow_name_split[0], '_electric')
                this_flow_name_split[0] = cut_suffix(this_flow_name_split[0], '_thermal')
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
                        this_comp_flows[bus] = component_flows[flow][:nb_intervals - nb_trailing_none]

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
                        this_comp_flows[bus] = [-this_val for this_val in
                                                component_flows[flow][:nb_intervals - nb_trailing_none]]

            # Replaces shorthand component names in the results with the official names for those listed.
            try:
                component_result.name = name_label_dict[component_result.name]
            except KeyError:
                print(component_result.name + ": is not defined in the label dict.")

            for this_bus in this_comp_flows:
                if this_bus not in busses_to_plot:
                    # If bus name didn't appear so far, add it to the list of busses.
                    busses_to_plot[this_bus] = dict()

                # Add the flow of this component to this bus.
                busses_to_plot[this_bus][component_result.name] = this_comp_flows[this_bus]

    if nb_trailing_none > 0:
        print(
            'The flow sequences have {} trailing None values. Did the optimization terminate?'.format(nb_trailing_none)
        )

    return busses_to_plot
