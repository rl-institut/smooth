from smooth.examples.example_VarBat.example_model_VarBat import mymodel
from multiprocessing import freeze_support
from smooth import save_results
from smooth import run_optimization

import logging
logging.getLogger('pyomo.core').setLevel(logging.ERROR)


def main():
    # Define the optimization parameter. This dict needs the following information:
    #  ga_params: Genetic algorithm parameters [dict].
    #  attribute_variation: Information on the attributes to vary [list].
    opt_params = dict()
    # Define the variables for the genetic algorithm:
    #  pop_size: Number of individuals in the population [-].
    #  n_gen: Number of generations that will be evaluated [-].
    #  n_core: Number of cores used in the optimization ('max' will use all of them) [-].
    #  plot_progress: show pareto front during each stop of the simulation [False].
    #  objectives: objective functions to maximize [2-tuple].
    #   Called with result of run_smooth.
    #   Negative sign for minimizing.
    #   Defaults to minimum of costs and emissions.
    #  objective_names: description of objectives [2-tuple]
    opt_params['ga_params'] = {
        'population_size': 16,
        'n_generation': 4,
        'n_core': 'max',
        'plot_progress': True,
        'post_processing': True,
        'save_intermediate_results': False,
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

    # E.g. the combination val_min = 5, val_max = 60 and val_step = 10 lead to
    # possible values 5, 15, 25, 35, 45 and 55.

    var_bat_type = {
        'comp_name': 'li_battery',
        'comp_attribute': 'battery_type',
        'val_min': 1,
        'val_max': 3,
        'val_step': 1
    }

    var_battery_capacity_bt1 = {
        'comp_name': 'li_battery',
        'comp_attribute': 'battery_capacity_bt1',
        'val_min': 0,
        'val_max': 50 * 1e3,
        'val_step': 10 * 1e3,
    }
    var_battery_capacity_bt2 = {
        'comp_name': 'li_battery',
        'comp_attribute': 'battery_capacity_bt2',
        'val_min': 50 * 1e3,
        'val_max': 1000 * 1e3,
        'val_step': 50 * 1e3,
    }
    var_battery_capacity_bt3 = {
        'comp_name': 'li_battery',
        'comp_attribute': 'battery_capacity_bt3',
        # 'val_min': 1 * 1e6,
        # 'val_max': 5 * 1e6,
        # 'val_step': 0.5 * 1e6,
        'val_min': 1000000,
        'val_max': 5000000,
        'val_step': 500000,
    }
    var_c_rate = {
        'comp_name': 'li_battery',
        'comp_attribute': 'c_rate',
        'val_min': 0.1,
        'val_max': 2,
        'val_step': 0.1,
    }

    # Add the attribute variation info to the optimization parameters.
    opt_params['attribute_variation'] = [var_bat_type,
                                         var_battery_capacity_bt1,
                                         var_battery_capacity_bt2,
                                         var_battery_capacity_bt3,
                                         var_c_rate
                                         ]

    # Run an optimization example.
    return run_optimization(opt_params, mymodel)


if __name__ == '__main__':
    freeze_support()
    optimization_results = main()
    save_results('optimization_result', optimization_results)
