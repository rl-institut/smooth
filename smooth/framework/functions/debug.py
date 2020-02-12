import pandas as pd

def get_df_debug(df_results, results_dict, new_df_results):
    # TODO delete experimental print(...)
    # EXMPERIMENTAL
    # print(results_dict)
    # print("------------------------------------------------------------------------------")
    # print([x for x in results_dict.keys()])
    # print(pd.DataFrame(np.array([[k[0].label, k[1].label] if k[1] is not None else [k[0].label, None]
    #                             for k, x in results_dict.items()])))
    # Extract oemof tuple, fixed (bool), min/max values scaled with the nominal value in case it is present
    operation_vals = [
        [
            k,
            x['scalars']['fixed'],
            x['scalars']['min'] * x['scalars']['nominal_value'],
            x['scalars']['max'] * x['scalars']['nominal_value'],
        ] for k, x in results_dict.items() if 'nominal_value' in x['scalars']
    ]
    operation_vals = pd.DataFrame(operation_vals, columns=['oemof_tuple', 'fixed', 'min', 'max'])
    # print(operation_vals)
    # DataFrame from last iteration merged with values from results dictionary
    df_debug = df_results[:][['value', 'variable_name', 'oemof_tuple']]
    df_debug[['from', 'to']] = pd.DataFrame(df_debug['oemof_tuple'].tolist(), index=df_debug.index)
    df_debug = pd.merge(left=df_debug, right=operation_vals, how='left', left_on='oemof_tuple',
                        right_on='oemof_tuple')
    # TODO include next values or delete code
    #cols = new_df_results.columns.to_list()
    #cols[1] = 'next_value'
    #new_df_results.columns = cols
    #new_df_results = new_df_results[['next_value', 'oemof_tuple']]
    #df_debug = pd.merge(left=df_debug, right=new_df_results, how='left', left_on='oemof_tuple',
    #                    right_on='oemof_tuple')
    # Move columns for better readability
    sel_cols = ['from', 'to', 'variable_name', 'fixed', 'min', 'value', 'max']
    df_debug = df_debug[sel_cols]

    return df_debug