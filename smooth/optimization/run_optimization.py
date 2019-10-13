# With this optimization tool, attributes of a smooth component can be optimized. For the optimization, a genetic
# algorithm (based on the DEAP package) is used.

import random
import numpy as np
import multiprocessing
import copy
from smooth.optimization.optimization_parameters import OptimizationParameters
from smooth.framework.run import run as run_smooth
from deap import base, creator, tools

def run_optimization(opt_config, model):
    # Find optimal component parameters of a smooth model that minimize the total annuity.
    # Parameter:
    #  opt_config: Configuration of the optimization [dict].
    #  model: smooth model [dict].

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

    def fitness_function(gen_of_individual):
        # The fitness function evaluates one gen combination of one individual.
        # Parameter:
        #  gen_of_individual: A list of binary values which are the gens of one individual [list].

        # If this individual was already evaluated, just give back the fitness value.
        if gen_of_individual.fitness.valid:
            return gen_of_individual.fitness.values

        # Get the values for each component of the gens given by the genetic algorithm.
        attribute_values = opt_params.get_attribute_values(gen_of_individual)
        # Make a copy of the original model (not by reference).
        this_model = copy.deepcopy(model)
        # Update the model according to the gens.
        for this_attribute in opt_params.attribute_var:
            # Loop through all components of the model dict till the right component is found.
            for this_comp in this_model['components']:
                if this_comp['name'] == this_attribute.comp_name:
                    # Get the attribute value for this attribute and delete it from the list of all attribute values.
                    this_value = attribute_values.pop(0)
                    # Change the value of that component according to the current gens.
                    this_comp[this_attribute.comp_attribute] = this_value

        return sum(gen_of_individual),
        # Now that the model is updated according to the genes given by the GA, smooth can be run.
        smooth_result = run_smooth(this_model)
        # As a fitness value, give back the summed up total annuity (which will be minimized) [EUR/a].
        annuity_tot = 0
        for this_comp in smooth_result:
            annuity_tot += this_comp.results['annuity_total']

        # For the DEAP package, the return value needs to be a tuple, thus the comma.
        return annuity_tot,

    tbx.register("evaluate", fitness_function)

    tbx.register("mate", tools.cxOnePoint)
    tbx.register("mutate", tools.mutFlipBit, indpb=0.01)
    tbx.register("select", tools.selTournament, tournsize=5)

    def set_fitness(_population):
        # Evaluate each individual of a population.
        # Parameter:
        #  population: List of individuals [list].

        """
        # Evaluate the fitness values for each individual.
        for i_individual in range(len(_population)):
            # Evaluate this population.
            this_fit_val = tbx.evaluate(_population[i_individual])
            # Save the fitness value in the individual.
            _population[i_individual].fitness.values = this_fit_val
        """

        pool = multiprocessing.Pool(processes=opt_params.ga_params.n_core)
        fitness_values = [None] * len(_population)

        for i_individual, this_individual in enumerate(_population):
            print(i_individual)
            fitness_values[i_individual] = pool.apply_async(tbx.evaluate(this_individual))
            print(fitness_values[i_individual])

        print(fitness_values)
        for i in fitness_values:
            print(i.get())
        pool.close()
        pool.join()


        #print(pool.map(tbx.evaluate, population))
        #for this_fit_val in pool.imap_unordered(tbx.evaluate, _population):
            # Evaluate this population.
            #this_fit_val = pool.apply_async(tbx.evaluate(_population[i_individual]))
            # Save the fitness value in the individual.
            #_population[i_individual].fitness.values = this_fit_val
            #print(this_fit_val)

        print('Generation evaluated.')

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
    # Compute the fitness values for the initial population.
    set_fitness(population)
    # quick look at the initial population,
    print(population[:5])
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

        # Calculate the fitness values for the current population.
        set_fitness(current_population)
        # Select the best individuals.
        population[:] = tbx.select(current_population, len(population))

        # set fitness on individuals in the population,
        stats.append(
            pull_stats(population, iteration))

        iteration += 1



"""



def EOQ(individual):

    i = to_int(
        ''.join((str(xi) for xi in individual)))

    return i,

creator.create("FitnessMin", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

tbx = base.Toolbox()

# Each individual will be a certain amount of bytes.
INDIVIDUAL_SIZE = 20

tbx.register("attr_int", random.randint, 0, 1)
tbx.register("individual",
             tools.initRepeat,
             creator.Individual,
             tbx.attr_int,
             n=INDIVIDUAL_SIZE)

tbx.register("population", tools.initRepeat, list, tbx.individual)

tbx.register("evaluate", EOQ)

tbx.register("mate", tools.cxOnePoint)
tbx.register("mutate", tools.mutFlipBit, indpb=0.01)
tbx.register("select", tools.selTournament, tournsize=5)


def set_fitness(population):
    fitnesses = [
        (individual, tbx.evaluate(individual))
        for individual in population
    ]

    for individual, fitness in fitnesses:
        individual.fitness.values = fitness


def pull_stats(population, iteration=1):
    fitnesses = [individual.fitness.values[0] for individual in population]
    return {
        'i': iteration,
        'mu': np.mean(fitnesses),
        'std': np.std(fitnesses),
        'max': np.max(fitnesses),
        'min': np.min(fitnesses)
    }

## create random population,
population = tbx.population(n=50)

## set fitness,
set_fitness(population)

## quick look at the initial population,
population[:5]

## globals,
stats = []

iteration = 1
while iteration < 51:

    current_population = list(map(tbx.clone, population))

    offspring = []
    for _ in range(10):
        i1, i2 = np.random.choice(range(len(population)), size=2, replace=False)

        offspring1, offspring2 = \
            tbx.mate(population[i1], population[i2])

        offspring.append(tbx.mutate(offspring1)[0])
        offspring.append(tbx.mutate(offspring2)[0])

    for child in offspring:
        current_population.append(child)

    ## reset fitness,
    set_fitness(current_population)

    population[:] = tbx.select(current_population, len(population))

    ## set fitness on individuals in the population,
    stats.append(
        pull_stats(population, iteration))

    iteration += 1


import seaborn as sns
import matplotlib.pyplot as plt

sns.set()

_ = plt.scatter(range(1, len(stats)+1), [ s['mu'] for s in stats ], marker='.')

_ = plt.title('average fitness per iteration')
_ = plt.xlabel('iterations')
_ = plt.ylabel('fitness')

plt.show()


def to_int(b):
    return int(b, 2)


sorted([(i, to_int(''.join((str(xi) for xi in individual)))) for i, individual in enumerate(population)][:10],
       key=lambda x: x[1], reverse=False)

"""