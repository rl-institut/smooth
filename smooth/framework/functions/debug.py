import pandas as pd
import numpy as np
import re

def get_df_debug(df_results, results_dict):
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
        ] if 'nominal_value' in x['scalars'] else # if 'nominal_storage_capacity' in x['scalars']
        [
            k,
            None,
            x['scalars']['min_storage_level'] * x['scalars']['nominal_storage_capacity'],
            x['scalars']['max_storage_level'] * x['scalars']['nominal_storage_capacity'],
        ]
        for k, x in results_dict.items()  if 'nominal_value' in x['scalars'] or 'nominal_storage_capacity' in x['scalars']
    ]

    [[[i, x['scalars'][i]] for i, item in x['scalars'].items() if i.endswith('conversion_factor')] for k, x in results_dict.items()]
    r = re.compile('.*conversion_factor.*')
    conversion_factors = np.array([[[k, i, x['scalars'][i]] for i, item in x['scalars'].items() if r.match(i)] for k, x in results_dict.items()])

    operation_vals = pd.DataFrame(operation_vals, columns=['oemof_tuple', 'fixed', 'min', 'max'])
    operation_vals['oemof_tuple'] = [tuple if tuple[1] != None else (tuple[0],) for tuple in
                                     operation_vals['oemof_tuple']]
    # DataFrame from last iteration merged with values from results dictionary
    df_debug = df_results[:][['value', 'variable_name', 'oemof_tuple']]
    df_debug[['from', 'to']] = pd.DataFrame(df_debug['oemof_tuple'].tolist(), index=df_debug.index)
    df_debug = pd.merge(left=df_debug, right=operation_vals, how='left', left_on='oemof_tuple',
                        right_on='oemof_tuple')
    # Move columns for better readability
    sel_cols = ['from', 'to', 'variable_name', 'fixed', 'min', 'value', 'max']
    df_debug = df_debug[sel_cols]

    return df_debug