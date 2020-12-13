import pandas as pd
from smooth.framework.functions.plot_results import plot_smooth_results


def get_df_debug(df_results, results_dict, new_df_results, index):
    """Generate debug info from results.

    :param df_results: results dataframe to compare against (e.g. last iteration)
    :type df_results: pandas dataframe
    :param results_dict: results dictionary from oemof.processing.parameter_as_dict
    :param new_df_results: newest results dataframe
    :type new_df_results: pandas dataframe
    :return: debug dataframe
    :rtype: pandas dataframe
    :raises TypeError: if df_results or results_dict is not set
    """

    # If no results were calculated yet, raise an exception
    if df_results is None or results_dict is None:
        raise TypeError

    # Extract oemof tuple, fixed (bool), min/max flow or storage-level values
    # scaled with the nominal value in case it is present
    operation_vals = [
        [
            k,
            x['scalars']['fixed'],
            x['scalars']['min'] * x['scalars']['nominal_value'],
            x['scalars']['max'] * x['scalars']['nominal_value'],
        ] if 'nominal_value' in x['scalars'] else
        [
            k,
            None,
            x['scalars']['min_storage_level'] * x['scalars']['nominal_storage_capacity'],
            x['scalars']['max_storage_level'] * x['scalars']['nominal_storage_capacity'],
        ]
        for k, x in results_dict.items() if 'nominal_value' in x['scalars'] or
                                            'nominal_storage_capacity' in x['scalars']
    ]

    operation_vals = pd.DataFrame(operation_vals, columns=['oemof_tuple', 'fixed', 'min', 'max'])
    operation_vals['oemof_tuple'] = [ot if ot[1] is not None else (ot[0],) for ot in
                                     operation_vals['oemof_tuple']]
    # Merge results DataFrame from last iteration with scalar values from results dictionary
    df_debug = df_results[:][['value', 'variable_name', 'oemof_tuple', 'timestep']]
    df_debug[['from', 'to']] = pd.DataFrame(df_debug['oemof_tuple'].tolist(), index=df_debug.index)
    df_debug = pd.merge(left=df_debug, right=operation_vals, how='left', left_on='oemof_tuple',
                        right_on='oemof_tuple')
    # Add base index from smooth to oemof timestep index
    df_debug['timestep'] = df_debug['timestep'] + index

    # Concatenate debug Dataframe with results of unfinished oemof iteration
    # (merging of different instances of oemof objects not working)
    new_df_results[['from', 'to']] = pd.DataFrame(
        new_df_results['oemof_tuple'].tolist(), index=new_df_results.index)
    new_df_debug = pd.DataFrame(new_df_results[:][['value', 'from', 'to']], columns=[
                                'value', 'from', 'to'])
    new_df_debug['variable_name'] = 'next'
    df_debug = pd.concat([df_debug, new_df_debug], axis=0)

    # Move columns for better readability
    sel_cols = ['from', 'to', 'variable_name', 'timestep', 'fixed', 'min', 'value', 'max']
    df_debug = df_debug[sel_cols]

    return df_debug


def save_debug(df_debug, components, index):
    """Save debug info, save to file with iteration index

    :param df_debug: debug dataframe
    :type df_debug: pandas dataframe
    :param components: result from run_smooth for plotting
    :type components: list of :class:`~smooth.components.component.Component`
    :param index: current smooth iteration index
    :type index: int
    """
    # Save to csv file
    df_debug.loc[:, df_debug.columns != 'oemof_tuple'].to_csv("debugDataframe_" +  str(index) + ".csv")
    print("Saved to debugDataframe.csv")


def show_debug(df_debug, components):
    """Print and plot debug info, save to file

    :param df_debug: debug dataframe
    :type df_debug: pandas dataframe
    :param components: result from run_smooth for plotting
    :type components: list of :class:`~smooth.components.component.Component`
    """
    print("------------------------------------------------------------------------------")
    with pd.option_context(
            "display.max_rows", 99,
            "display.max_columns", 12,
            'display.max_colwidth', 0):
        print(df_debug)
    print("------------------------------------------------------------------------------")
    # Save to csv file
    df_debug.loc[:, df_debug.columns != 'oemof_tuple'].to_csv("debugDataframe.csv")
    print("Saved to debugDataframe.csv")

    #plot_smooth_results(components)
    from eMetroBus_specific.plotting_dict import comp_dict_german
    from eMetroBus_specific.plot_results_eMetroBus_v6 import plot_smooth_results
    path = '\\examples\\UHAL_v2_MPC\\UHAL_TS1_v2\\results_and_plots\\'
    # filename = 'Opt_1D1h_MaxPV_bat2M8kWh'
    filename = 'Opt_1D1m_minBat'
    filepath = path + filename + '\\'
    plot_smooth_results(components, False, filepath, filename, comp_dict_german)


def plot_mpc(debug_list, h):
    import matplotlib.pyplot as plt

    for d_df in debug_list:
        df = d_df[h:2 * h - 1]  # [96:120][121:144][24:46]#[d_df['to']=='li_battery']
        plt.subplot(311)
        plt.plot(df['timestep'], df['value'])  # , c=(0,0,1-(df.iloc[0]['timestep'])/24, 0.1))

        df = d_df[5 * h + 1:6 * h]  # [24:46]#[d_df['to']=='li_battery']
        plt.subplot(312)
        plt.plot(df['timestep'], df['value'])

        df = d_df[4 * h:5 * h]  # [121:144][24:46]#[d_df['to']=='li_battery']
        plt.subplot(313)
        plt.plot(df['timestep'], df['value'])

    plt.show()
