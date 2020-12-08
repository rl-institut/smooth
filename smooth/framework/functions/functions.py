import os
import importlib
import pandas as pd
import re


def read_data_file(path, filename, csv_separator, column_title):
    """Function to read the input data files.

    :param path: path where the csv file is located
    :type path: string
    :param filename: name of csv file
    :type filename: string
    :param csv_separator: separator of csv data
    :type csv_separator: character
    :param column_title: title of data column
    :type column_title: string
    :return: column of data from csv file
    :rtype: pandas dataframe
    """
    file_path = os.path.join(path, filename)
    # create specific string for chosen data type
    data = pd.read_csv(file_path, sep=csv_separator, usecols=[column_title], encoding='latin-1')
    return data


def get_date_time_index(start_date, n_intervals, step_size):
    """Function defining the parameters for perfect/myopic foresight.

    :param start_date: the first evaluated time period, e.g. '1/1/2019'
    :type start_date: string
    :param n_intervals: number of time periods
    :type n_intervals: integer
    :param step_size: length of one time step in minutes
    :type step_size: number
    :return: *n_intervals* dates, each *step_size* minutes apart
    :rtype: pandas `DateTimeIndex <https://pandas.pydata.org/ \
    pandas-docs/stable/reference/api/pandas.DatetimeIndex.html>`_
    """
    date_time_index = pd.date_range(start_date, periods=n_intervals, freq='{}min'.format(step_size))
    return date_time_index


def interval_time_index(date_time_index, i_interval):
    """Function to divide the set date time index into hourly intervals.

    This function seems to be unused.

    :param date_time_index: chosen date range for the model
    :type date_time_index: DateTimeIndex
    :param i_interval: current interval index
    :type i_interval: integer
    :return: pandas `DateTimeIndex <https://pandas.pydata.org/pandas-docs/stable/ \
    reference/api/pandas.DatetimeIndex.html>`_ for current interval
    """
    this_time_index = date_time_index[i_interval: (i_interval + 1)]
    return this_time_index


def get_sim_time_span(n_interval, step_size):
    """Calculate the time span of the simulation.

    :param n_interval: number of intervals
    :type n_interval: integer
    :step_size: length of one time step in minutes
    :type step_size: number
    :return: time delta in minutes
    :rtype: number
    """
    return n_interval * step_size


def create_component_obj(model, sim_params):
    """Create components from model.

    :param model: smooth model
    :type model: dictionary
    :param sim_params: simulation parameters
    :type sim_params: :class:`~smooth.framework.simulation_parameters.SimulationParameters`
    :return: list of components in model
    :rtype: list of :class:`~smooth.components.component.Component`
    """
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
            raise ValueError('Invalid component type name "{}". '
                             'Only lower case letters, numbers and underscores are allowed.'
                             .format(this_comp_type))
        # Import the module of the component.
        this_comp_module = importlib.import_module('smooth.components.component_' + this_comp_type)
        # Convert component type from snake_case to CamelCase to get class name
        class_name = ''.join(x.capitalize() for x in this_comp_type.split('_'))
        # Load the class (which by convention has a name with a capital first
        # letter and camel case).
        this_comp_class = getattr(this_comp_module, class_name)
        # Initialize the component.
        this_comp_obj = this_comp_class(this_comp)
        # Check if this component is valid.
        this_comp_obj.check_validity()
        # Add this component to the list containing all components.
        components.append(this_comp_obj)

    return components


def replace_at_idx(tup, i, val):
    """Replaces a value at index *i* of a tuple *tup* with value *val*

    :param tup: tuple to be updated
    :param i: index at which the value should be replaced
    :type i: integer
    :param val: new value at index i
    :type val: value
    :return: new tuple with replaced value
    """
    tup_list = list(tup)
    tup_list[i] = val

    return tuple(tup_list)


def cut_suffix(name, suffix):
    """Cuts off the *suffix* from *name* string, if it ends with it

    :param name: original name from which suffix will be cut off
    :type name: string
    :param suffix: string to be removed
    :return: string without suffix
    """
    if isinstance(name, str) and name.endswith(suffix):
        name = name[:-len(suffix)]

    return name


def cut_suffix_loop(name_tuple, suffix_list):
    """Cuts off all suffixes present in *suffix_list* from names in *name_tuple*

    :param name_tuple: tuple of strings from which suffixes will be cut off
    :param suffix_list: list of strings to be removed
    :return: updated *name_tuple*
    :rtype: tuple of strings
    """
    for i in range(len(name_tuple)):
        for s in suffix_list:
            new_name = cut_suffix(name_tuple[i], s)
            name_tuple = replace_at_idx(name_tuple, i, new_name)

    return name_tuple


def extract_flow_per_bus(smooth_result, name_label_dict):
    """Extract dict containing the busses that will be plotted.

    :param smooth_result: result from run_smooth
    :type smooth_result: list of :class:`~smooth.components.component.Component`
    :param name_label_dict: dictionary
        with key being a component name in the model and value the name to display
    :return: dictionary of all busses from the model with their flow values over time
    """
    # Creates empty dict which will later contain the busses that will be plotted.
    busses_to_plot = dict()
    nb_trailing_none = 0

    for component_result in smooth_result:
        if hasattr(component_result, 'flows'):
            # Track the flows of this component.
            this_comp_flows = dict()
            component_flows = component_result.flows
            for flow_tuple, flow in component_flows.items():
                # Identify the number of trailing None values in case the
                # optimization stopped before termination
                nb_intervals = len(flow)
                nb_trailing_none = nb_intervals
                for flow_val in flow:
                    if flow_val is not None:
                        nb_trailing_none -= 1
                    else:
                        break
                # check if it's a chp component which consists of two oemof models
                # if so get rid of the ending '_electric' or '_thermal'
                flow_tuple = cut_suffix_loop(flow_tuple, ['_thermal', '_electric'])
                if flow_tuple[0] == component_result.name:
                    # Case: Component flows into bus.
                    bus = flow_tuple[1]
                    # Check if this component already has a flow with this bus.
                    if bus in this_comp_flows:
                        updated_bus_list = []
                        for i_val in range(len(this_comp_flows[bus]) - nb_trailing_none):
                            # Get the summed up value.
                            this_val = this_comp_flows[bus][i_val] + flow[i_val]
                            updated_bus_list.append(this_val)
                        # Override the old bus list with the updated one.
                        this_comp_flows[bus] = updated_bus_list
                    else:
                        # Case: Component has no flow with this bus yet.
                        this_comp_flows[bus] = flow[:nb_intervals - nb_trailing_none]

                else:
                    # Case: Component takes from bus.
                    bus = flow_tuple[0]
                    # Check if this component already has a flow with this bus.
                    if bus in this_comp_flows:
                        updated_bus_list = []
                        for i_val in range(len(this_comp_flows[bus]) - nb_trailing_none):
                            # Get the summed up value.
                            this_val = this_comp_flows[bus][i_val] - flow[i_val]
                            updated_bus_list.append(this_val)
                        # Override the old bus list with the updated one.
                        this_comp_flows[bus] = updated_bus_list
                    else:
                        # Case: Component has no flow with this bus yet.
                        flow_range = flow[:nb_intervals - nb_trailing_none]
                        this_comp_flows[bus] = [-this_val for this_val in flow_range]

            # get name from dictionary
            # set default component name
            name = component_result.name
            try:
                # set name from dictionary
                name = name_label_dict[name]
            except KeyError:
                print("{}: is not defined in the label dict.".format(name))

            for this_bus in this_comp_flows:
                if this_bus not in busses_to_plot:
                    # If bus name didn't appear so far, add it to the list of busses.
                    busses_to_plot[this_bus] = dict()

                # Add the flow of this component to this bus.
                busses_to_plot[this_bus][name] = this_comp_flows[this_bus]

    if nb_trailing_none > 0:
        print(
            'The flow sequences have {} trailing None values. Did the optimization terminate?'
            .format(nb_trailing_none)
        )

    return busses_to_plot


def choose_valid_dict(component, var_dict):
    """Function to select a valid dict (capex / fix_emissions) depending on the value
    of an attribute of the specific component.

    :param component: object of this component
    :type component: class:`~smooth.components.component.Component`
    :param var_dict: dict object (capex/fix_emissions) of this component
    :type var_dict: dict
    :return: Valid dictionary (capex/fix_emissions) for the actual value
        of the depending parameter of the component
    """

    low_thresholds = [d['low_threshold'] for d in var_dict['var_dicts']]
    high_thresholds = [d['high_threshold'] for d in var_dict['var_dicts']]
    for i in range(len(low_thresholds)):
        assert low_thresholds[i] < high_thresholds[i],\
            'The threshold range of a variable_dict (capex or emissions) for component \''\
            + component.name + '\' is either zero or negative.'
        if i < len(low_thresholds) - 1:
            assert low_thresholds[i] <= low_thresholds[i + 1], \
                'A variable_dict (capex or emissions) of component \'' \
                + component.name + '\' is not defined with thresholds in ascending order.'
            assert high_thresholds[i] <= low_thresholds[i + 1], \
                'A variable_dict (capex or emissions) of component \'' \
                + component.name + '\' has an overlap in its threshold definition.'

    success = False
    for i in range(len(var_dict['var_dicts'])):
        if (getattr(component, var_dict['var_dict_dependency'])
            >= var_dict['var_dicts'][i]['low_threshold']) & \
            (getattr(component, var_dict['var_dict_dependency'])
             < var_dict['var_dicts'][i]['high_threshold']):
            var_dict = var_dict['var_dicts'][i]
            success = True
            break
    assert success, \
        'No suitable capex / fix_emissions found for component ' + component.name + ' with ' + \
        var_dict['var_dict_dependency'] + ' = ' \
        + str(getattr(component, var_dict['var_dict_dependency']))
    return var_dict
