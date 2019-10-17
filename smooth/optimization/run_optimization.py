# With this optimization tool, attributes of a smooth component can be optimized. For the optimization, a genetic
# algorithm (based on the DEAP package) is used.

import random
import numpy as np
import multiprocessing
import copy
import math
from smooth.optimization.optimization_parameters import OptimizationParameters
from smooth import run_smooth
from deap import base, creator, tools


# Define if you want to save all smooth results of each individual evaluated. This can lead to big result files, in a
# test run, the results of 100 individuals was ~500 MB, while the result file with only the smooth result saved for the
# best individual was ~5 MB.
save_all_smooth_results = False


def fitness_function(_i_individual, _individual, model, opt_params):
    # The fitness function evaluates one gen combination of one individual.
    # Parameter:
    #  _i_individual: Index of this individual [int].
    # _individual: A shadow of a deap individual [ShadowIndividual].
    # model: description of the smooth model.

    # If this individual was already evaluated, just give back the fitness value.
    if _individual.fitness.valid:
        return [_i_individual, _individual]

    # Get the values for each component of the gens given by the genetic algorithm.
    attribute_values = opt_params.get_attribute_values(_individual.gen)
    # Make a copy of the original model (not by reference).
    this_model = copy.deepcopy(model)
    # Update the model according to the gens.
    for this_attribute in opt_params.attribute_var:
        # Loop through all components of the model dict till the right component is found.
        for this_comp in this_model['components']:
            if this_comp['name'] == this_attribute.comp_name:
                # Get the attribute value for this attribute and delete it from the list of all attribute values.
                this_value = attribute_values.pop(0)
                # Save the value in this component for later use.
                this_attribute.this_val = this_value
                # Change the value of that component according to the current gens.
                this_comp[this_attribute.comp_attribute] = this_value

    # Now that the model is updated according to the genes given by the GA, smooth can be run.
    try:
        smooth_result = run_smooth(this_model)
        # As a fitness value, give back the summed up total annuity (which will be minimized) [EUR/a].
        annuity_tot = 0
        for this_comp in smooth_result:
            annuity_tot += this_comp.results['annuity_total']

    except:
        # The smooth run failed. Therefore the fitness value is set to infinity.
        # ToDo: Check if setting the fitness value to infinity is a good way to handle bad individuals. Maybe this could
        # ToDo: be handled in a way where the genetic algorithm can extract information out of the failed result.
        print('------------------------------------------------------------------------------------Evaluation canceled')
        # Case: Smooth couldn't run through, thus a bad fitness value has to be assigned.
        annuity_tot = float('inf')
        smooth_result = None

    # For the DEAP package, the fitness value needs to be a tuple, thus the comma.
    _individual.fitness.valid = True
    _individual.fitness.values = annuity_tot,
    _individual.smooth_result = smooth_result
    _individual.attribute_variation = opt_params.attribute_var
    return [_i_individual, _individual]


class TrackIndividuals:
    # Track all individuals that ever have been calculated to prevent double calculations. An object of this class will
    # be the output of the optimization run.
    def __init__(self):
        # Dict of all results that have been done calculated so far. The key of one individual is the decimal number of
        # its binary gens (e.g. 0 0 1 0 1 --> key is 5)
        self.individuals_evaluated = dict()
        # The best fitness value.
        self.best_fit_val = None
        # Index of the individual with the best fitness value.
        self.i_best_fit_val = None
        # Gens of the individual with the best fitness value.
        self.best_gens = None
        # Smooth result of the individual with the best fitness value.
        self.best_smooth_result = None
        # Safe the stats of a run.
        self.stats = None

    def set_fitness_value(self, individual):
        # Set the fitness value of an individual if that individual was already evaluated.
        # Parameters:
        #  individual: An individual object from deap [individual]

        # Get the integer value of the gens [int].
        int_val = self.get_int(list(individual))
        # Check if the int value is a key in the dictionary.
        if int_val in self.individuals_evaluated and not individual.fitness.valid:
            # Return the fitness value.
            individual.fitness.values = self.individuals_evaluated[int_val].fitness.values

    def set_stats(self, stats):
        # After an optimization run the states are saved to the tracked individuals (which are then given out).
        self.stats = stats

    def add_individual(self, individual):
        # Add an individual to the dictionary of evaluated individuals if it wasn't evaluated yet.
        # Parameters:
        #  individual: An individual object from deap [individual]

        # Get the integer value of the gens.
        int_val = self.get_int(individual.gen)

        if int_val not in self.individuals_evaluated:
            # If this individual has the best fitness value so far, save it as the best.
            if self.best_fit_val is None or individual.fitness.values < self.best_fit_val:
                self.best_fit_val = individual.fitness.values
                self.i_best_fit_val = int_val
                self.best_gens = individual.gen
                self.best_smooth_result = individual.smooth_result

            # Then save the individual as an individual evaluated. If not all smooth results are supposed to be saved,
            # delete the smooth result first (this drastically reduces the size of the result file).
            if not save_all_smooth_results:
                individual.smooth_result = None

            # Add the individual to the list of evaluated individuals.
            self.individuals_evaluated[int_val] = IndividualShadow(
                individual.gen, individual.fitness.values, individual.smooth_result, individual.attribute_variation)


    def get_int(self, gen):
        # Calculate an integer by a given list of binary values.
        # Parameter:
        #  gen: A gen sequence of binary values [list].

        # Convert the genes to a string and then to an integer.
        binary_string = ''.join((str(this_gen) for this_gen in gen))
        # Return the integer value [int]
        return int(binary_string, 2)


class IndividualShadow:
    # While there are problems with pickling the "Individual" class from deap, a shadow for an individual can be created
    # in order to use multiprocessing (which uses pickling).
    def __init__(self, gen, fitness_val, smooth_result=None, attribute_var=None):
        # The gen of the individual as list of binary values [list].
        self.gen = gen
        # The fitness value [Fitness object].
        self.fitness = Fitness(fitness_val)
        # The results of the smooth run [list].
        self.smooth_result = smooth_result
        # The parameter that were varied by the genetic algorithm [].
        self.attribute_variation = attribute_var


class Fitness:
    # Track the fitness values in the style the "Individual" class from deap does.
    def __init__(self, fitness_val):
        self.values = fitness_val
        if fitness_val is None:
            self.valid = False
        else:
            self.valid = True


class GenerationEvaluationResult:
    # This class tracks all the fitness evaluation results that are calculated in parallel.
    def __init__(self, n_individuals):
        self.individuals = [None] * n_individuals

    def update_result(self, result):
        # This function is the callback function to the parallel call of the fitness function.
        self.individuals[result[0]] = result[1]


def compute_fitness_values(_population, model, opt_params):
    # While the deap type "individuals" leads to problems with the multiprocessing toolbox, the information is
    # extracted.
    population_shadow = []
    for this_population in _population:
        if this_population.fitness.valid:
            fitness_value = this_population.fitness.values
        else:
            fitness_value = None

        # Get the genes of this population [list].
        this_gens = list(this_population)

        population_shadow.append(IndividualShadow(this_gens, fitness_value))

    # Generate a result object that will catch the results of the function evaluation.
    individuals_evaluated = GenerationEvaluationResult(len(_population))
    # Generate a pool for using multiple cores.
    pool = multiprocessing.Pool(processes=opt_params.ga_params.n_core)
    # Start the fitness function evaluations in parallel.
    for i_individual, this_individual in enumerate(population_shadow):
        # Asynchronously call the fitness function for each individual. The results are saved by calling the callback
        # function.
        pool.apply_async(fitness_function, (i_individual, this_individual, model, opt_params),
                         callback=individuals_evaluated.update_result)

    # Close and join the pool make sure that the code is not continuing before each evaluation is finished.
    pool.close()
    pool.join()

    # Return the evaluated individuals.
    return individuals_evaluated


def run_optimization(opt_config, _model):
    # Find optimal component parameters of a smooth model that minimize the total annuity.
    # Parameter:
    #  opt_config: Configuration of the optimization [dict].
    #  model: smooth model [dict].
    #  result_file_name: If given, the results will be saved to the file preceded by the current time [str].

    # Create an object containing all the relevant information for the genetic algorithm.
    opt_params = OptimizationParameters()
    opt_params.set_params(opt_config)

    # Set up a minimization problem.
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMin)
    tbx = base.Toolbox()

    # Number of bytes that make up the gens of an individual [-].
    n_gen_per_individual = opt_params.n_gen_total

    # Set each single gen to be initialized as a random value 0 or 1.
    tbx.register("attr_int", random.randint, 0, 1)
    # Define the properties of one individual.
    tbx.register("individual",
                 tools.initRepeat,
                 creator.Individual,
                 tbx.attr_int,
                 n=n_gen_per_individual)
    # Define the population.
    tbx.register("population", tools.initRepeat, list, tbx.individual)

    def map_fitness(this_evaluated_results):
        return this_evaluated_results.fitness.values

    # Set the evaluation function, the mating processing, the mutating process and the selection process for deap.
    tbx.register("evaluate", map_fitness)
    tbx.register("mate", tools.cxOnePoint)
    tbx.register("mutate", tools.mutFlipBit, indpb=0.01)
    tbx.register("select", tools.selTournament, tournsize=5)

    # Create an object that will track all evaluated individuals.
    track_individuals = TrackIndividuals()

    def set_fitness(_population):
        # Evaluate each individual of a population.
        # Parameter:
        #  population: List of individuals [list].

        # While there is a problem with using deap with computing on multiple cores, first the fitness values are
        # evaluated in parallel and the result is given back.
        individuals_evaluated = compute_fitness_values(_population, _model, opt_params)

        # The fitness function used by deap only maps the results already generated in the last step.
        for i_individual in range(len(_population)):
            # Assign the fitness value to this individual. Fitness value must be given as tuple (thus the comma).
            _population[i_individual].fitness.values = tbx.evaluate(individuals_evaluated.individuals[i_individual])

        # Add all evaluated tracked individuals to track_individuals.
        for _this_individual in individuals_evaluated.individuals:
            track_individuals.add_individual(_this_individual)

    def pull_stats(_population, _iteration=1):
        fitnesses = [individual.fitness.values[0] for individual in _population]
        return {
            'i': _iteration,
            'mu': np.mean(fitnesses),
            'std': np.std(fitnesses),
            'max': np.max(fitnesses),
            'min': np.min(fitnesses)
        }

    # Crate a random initial population.
    population = tbx.population(n=opt_params.ga_params.population_size)

    print('\n+++++++ START GENETIC ALGORITHM +++++++')
    print('The optimization parameters chosen are:')
    print('  population_size: {}'.format(opt_params.ga_params.population_size))
    print('  n_generation:    {}'.format(opt_params.ga_params.n_generation))
    print('  n_core:          {}'.format(opt_params.ga_params.n_core))
    print('+++++++++++++++++++++++++++++++++++++++\n')

    # Compute the fitness values for the initial population.
    set_fitness(population)
    # If no evaluation was successful, throw an error.
    if track_individuals.best_fit_val == (float('inf'),):
        raise ValueError('No evaluation of the initial population was successful!')

    # globals,
    stats = []

    # Now run all populations.
    iteration = 1
    while iteration <= opt_params.ga_params.n_generation:
        # Get the current population.
        current_population = list(map(tbx.clone, population))
        # Get offspring of the current population.
        offspring = []
        for _ in range(10):
            i1, i2 = np.random.choice(range(len(population)), size=2, replace=False)
            # Mate two individuals to generate two offspring.
            offspring1, offspring2 = \
                tbx.mate(population[i1], population[i2])
            # While the fitness values of the parents are in the children, they have to be deleted.
            del offspring1.fitness.values
            del offspring2.fitness.values
            # Save the new offspring individuals to the offspring list.
            offspring.append(tbx.mutate(offspring1)[0])
            offspring.append(tbx.mutate(offspring2)[0])

        for child in offspring:
            current_population.append(child)

        # Set the fitness values for each individual in the population that has already been evaluated.
        for this_individual in current_population:
            track_individuals.set_fitness_value(this_individual)

        # Calculate the fitness values for the current population.
        set_fitness(current_population)

        # Select the best individuals.
        population[:] = tbx.select(current_population, len(population))

        # set fitness on individuals in the population,
        stats.append(
            pull_stats(population, iteration))

        print('Iteration {} finished. Best fit. val: {} Avg. fit. val: {}'.format(
            iteration, math.floor(stats[-1]['min']), math.floor(stats[-1]['mu'])))

        iteration += 1

    print('\n+++++++ GENETIC ALGORITHM FINISCHED +++++++')
    print('The best individual is:')
    print('  fit_val: {}'.format(track_individuals.best_fit_val))
    best_attribute_vals = opt_params.get_attribute_values(track_individuals.best_gens)
    for this_attribute in opt_params.attribute_var:
        print(' attribute {} - {} value: {}'.format(
            this_attribute.comp_name, this_attribute.comp_attribute, best_attribute_vals.pop(0)))

    print('+++++++++++++++++++++++++++++++++++++++++++\n')

    # Save the stats in the output.
    track_individuals.set_stats(stats)

    return track_individuals
