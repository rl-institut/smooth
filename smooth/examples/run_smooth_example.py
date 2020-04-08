from smooth.examples.example_model import mymodel
from smooth import run_smooth
from smooth import print_smooth_results
from smooth import save_results
from smooth import plot_smooth_results
from smooth.examples.example_plotting_dicts import comp_dict

# Run an example.
smooth_result, status = run_smooth(mymodel)
plot_smooth_results(smooth_result, comp_dict)

from smooth.framework.functions.plot_interactive_results import plot_interactive_smooth_results
plot_interactive_smooth_results(smooth_result)
