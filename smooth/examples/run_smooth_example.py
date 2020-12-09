"""
This example shows how a simulation in SMOOTH can be defined.

* The :func:`~smooth.framework.run_smooth` function is called which instigates
  the simulation, and the results are saved in the *smooth_result* parameter.

* The results are plotted using the *smooth_result* and the dictionary of
  choice for the axis/labels with the :func:`~smooth.framework.functions.plot_results`
  function.

* The results are printed in the terminal by calling the
  :func:`~smooth.framework.functions.print_results` function.

* The results are saved as a pickle file with the
  :func:`~smooth.framework.functions.save_results` function, that can later be
  loaded with the :func:`~smooth.framework.functions.load_results` function.

* The costs of the external components are calculated by using the
  :func:`~smooth.framework.functions.calculate_external_costs.costs_for_ext_components`
  function.
"""
from smooth.examples.example_model import mymodel

from smooth import run_smooth
from smooth import plot_smooth_results
from smooth import print_smooth_results
from smooth import save_results
from smooth.framework.functions.calculate_external_costs import costs_for_ext_components
from smooth.examples.example_plotting_dicts import comp_dict_german

if __name__ == '__main__':
    # Run an example.
    smooth_result, status = run_smooth(mymodel)
    plot_smooth_results(smooth_result, comp_dict_german)
    print_smooth_results(smooth_result)
    save_results('example_results', smooth_result)
    external_components = costs_for_ext_components(mymodel)

    print('done')
