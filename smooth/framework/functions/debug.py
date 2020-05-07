import pandas as pd
from smooth.framework.functions.plot_results import plot_smooth_results


def get_df_debug(df_results, results_dict, new_df_results):
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
    df_debug = df_results[:][['value', 'variable_name', 'oemof_tuple']]
    df_debug[['from', 'to']] = pd.DataFrame(df_debug['oemof_tuple'].tolist(), index=df_debug.index)
    df_debug = pd.merge(left=df_debug, right=operation_vals, how='left', left_on='oemof_tuple',
                        right_on='oemof_tuple')

    # Concatenate debug Dataframe with results of unfinished oemof iteration
    # (merging of different instances of oemof objects not working)
    new_df_results[['from', 'to']] = pd.DataFrame(new_df_results['oemof_tuple'].tolist(), index=new_df_results.index)
    new_df_debug = pd.DataFrame(new_df_results[:][['value', 'from', 'to']], columns=['value', 'from', 'to'])
    new_df_debug['variable_name'] = 'next'
    df_debug = pd.concat([df_debug, new_df_debug], axis=0)

    # Move columns for better readability
    sel_cols = ['from', 'to', 'variable_name', 'fixed', 'min', 'value', 'max']
    df_debug = df_debug[sel_cols]

    return df_debug


def show_debug(df_debug, components):
    print("------------------------------------------------------------------------------")
    with pd.option_context("display.max_rows", 99, "display.max_columns", 12, 'display.max_colwidth', 0):
        print(df_debug)
    print("------------------------------------------------------------------------------")
    # Save to csv file
    df_debug.loc[:, df_debug.columns != 'oemof_tuple'].to_csv("debugDataframe.csv")
    print("Saved to debugDataframe.csv")

    plot_smooth_results(components)