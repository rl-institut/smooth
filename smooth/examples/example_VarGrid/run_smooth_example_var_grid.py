from smooth.examples.example_VarGrid.example_model_var_grid import mymodel
from smooth.examples.example_VarGrid.example_plotting_dict_var_grid import comp_dict_german
from smooth import run_smooth
from smooth import plot_smooth_results
from smooth import print_smooth_results


if __name__ == '__main__':
    # Run an example.
    smooth_result, status = run_smooth(mymodel)
    plot_smooth_results(smooth_result, comp_dict_german)
    print_smooth_results(smooth_result)
