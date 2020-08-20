from smooth.framework.functions.load_results import load_results
from smooth.framework.functions.calculate_external_costs import calculate_costs_for_external_components
from smooth.examples.example_model_external_components import mymodel

result_file_name = '2020-08-20_12-17-31_external_components_test.pickle'

external_components = calculate_costs_for_external_components(mymodel)
optimization_results = load_results(result_file_name)

print('done')
