from smooth.examples.example_dict_model import mymodel
from smooth import run_smooth
from smooth import plot_smooth_results
from smooth.examples.example_plotting_dicts import comp_dict

# Run an example.
smooth_result, status = run_smooth(mymodel)
plot_smooth_results(smooth_result, comp_dict)
