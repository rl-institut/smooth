from smooth.examples.example_model_external_components import mymodel
from smooth import run_smooth
from smooth import print_smooth_results
from smooth import save_results
from smooth import plot_smooth_results
from smooth.framework.functions.calculate_external_costs import calculate_costs_for_external_components

# Run an example.
smooth_result = run_smooth(mymodel)

external_components = calculate_costs_for_external_components(mymodel)

print_smooth_results(smooth_result)

plot_smooth_results(smooth_result)

