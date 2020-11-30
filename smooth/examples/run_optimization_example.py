"""
This example demonstrates how to use the optimization algorithm.

1. Define the optimization parameters. This dict needs the following information:

* genetic algorithm parameters
* information on the attributes to vary

2. Define the variables for the genetic algorithm:

* number of individuals in the population
* number of generations that will be evaluated
* number of cores used in the optimization
* the visibility of the pareto front
* the occurence of post-processing
* the objective functions to maximise/minimise
* whether or not intermediate results should be saved
* whether or not the detailed final results should be saved

For instance, in the below example of the variables being defined, the
optimization is based on minimizing costs and emissions, evaluating 8
individuals for 2 generations with the use of the maximum possible
number of cores available.

.. code:: bash

    opt_params['ga_params'] = {
        'population_size': 8,
        'n_generation': 2,
        'n_core': 'max',
        'plot_progress': True,
        'post_processing': True,
        'save_intermediate_results': True,
        'objectives': (
            lambda x: -sum([c.results["annuity_total"] for c in x]),
            lambda x: -sum([c.results["annual_total_emissions"] for c in x]),
        ),
        'objective_names': ('costs', 'emissions'),
        'SAVE_ALL_SMOOTH_RESULTS': False,
    }

3. Define the attribute variation information that will be used by the genetic algorithm:

* component name
* component attribute that will be varied in the optimization
* the range (minimum and maximum value) to be considered in the variation process
* the stepsize to be considered within the range

As an example, here is how the variation of an electrolyzer's power between 100 kW
and 2000 kW with a stepsize of 50 kW is defined:

.. code:: bash

    var_ely_power = {
        'comp_name': 'this_ely',
        'comp_attribute': 'power_max',
        'val_min': 100e3,
        'val_max': 2000e3,
        'val_step': 50e3
    }

4. Add the attribute variation information to the optimization parameters:

.. code:: bash

    opt_params['attribute_variation'] = [var_ely_power, var_storage_capacity]
"""


from smooth.examples.example_model import mymodel
from multiprocessing import freeze_support
from smooth import run_optimization, save_results

import logging
logging.getLogger('pyomo.core').setLevel(logging.ERROR)


def main():
    """
    """
    # Define the optimization parameters. This dict needs the following information:
    #  ga_params: Genetic algorithm parameters [dict].
    #  attribute_variation: Information on the attributes to vary [list].
    opt_params = dict()
    # Define the variables for the genetic algorithm:
    #  pop_size: Number of individuals in the population [-].
    #  n_gen: Number of generations that will be evaluated [-].
    #  n_core: Number of cores used in the optimization ('max' will use all of them) [-].
    #  plot_progress: show pareto front during each stop of the simulation [False].
    #  ignore_zero:  Ignores components if the optimized value is zero for an individual [False]
    #  objectives: objective functions to maximize [2-tuple].
    #   Called with result of run_smooth.
    #   Negative sign for minimizing.
    #   Defaults to minimum of costs and emissions.
    #  objective_names: description of objectives [2-tuple]
    opt_params['ga_params'] = {
        'population_size': 8,
        'n_generation': 2,
        'n_core': 'max',
        'plot_progress': True,
        'post_processing': True,
        'save_intermediate_results': True,
        'ignore_zero': True,
        'objectives': (
            lambda x: -sum([c.results["annuity_total"] for c in x]),
            lambda x: -sum([c.results["annual_total_emissions"] for c in x]),
        ),
        'objective_names': ('costs', 'emissions'),
        'SAVE_ALL_SMOOTH_RESULTS': False,
    }
    # Define the attribute variation information that will be used by the genetic algorithm.
    #  comp_name: Name of the component [string].
    #  comp_attribute: Name of the attribute to be varied [string].
    #  val_min: Min. value in variation process [int/float].
    #  val_max: Max. value in variation process [int/float].
    #  val_step: Step size in variation process [int/float].
    #
    # E.g. the combination val_min = 5, val_max = 60 and val_step = 10 lead to
    # possible values 5, 15, 25, 35, 45 and 55.
    var_ely_power = {
        'comp_name': 'this_ely',
        'comp_attribute': 'power_max',
        'val_min': 100e3,
        'val_max': 2000e3,
        'val_step': 50e3
    }
    var_storage_capacity = {
        'comp_name': 'h2_storage',
        'comp_attribute': 'storage_capacity',
        'val_min': 0,
        'val_max': 2000,
        'val_step': 50
    }
    # Add the attribute variation info to the optimization parameters.
    opt_params['attribute_variation'] = [var_ely_power, var_storage_capacity]

    # Run an optimization example.
    return run_optimization(opt_params, mymodel)


if __name__ == '__main__':
    freeze_support()
    optimization_results = main()
    save_results('optimization_result', optimization_results)
