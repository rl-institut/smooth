from multiprocessing import Pool, cpu_count
from deap import base, creator, tools
from random import seed, randint, random
import numpy as np

from smooth import run_smooth

class AttributeVariation:
    # Class that contain all information about the attribute that is varied by the genetic algorithm.
    # recommended attributes: comp_name, comp_attribute, val_min, val_max
    def __init__(self, iterable=(), **kwargs):
        self.__dict__.update(iterable, **kwargs)

class OptimizationResult:
    # Class to store result from GA
    individuals_evaluated = dict() # unused
    best_fit_val = None # best score
    i_best_fit_val = 0 # index of best indivdual: always first
    best_gens = None # best genes
    best_smooth_result = None # best smooth result
    stats = [] # statistics for each generation

    def __init__(self, iterable=(), **kwargs):
        self.__dict__.update(iterable, **kwargs)

class Optimization:

    SAVE_ALL_SMOOTH_RESULTS = False

    def __init__(self, iterable=(), **kwargs):
        # defaults
        self.weights = (1.0,)
        self.generation = {"select": 2, "crossover": 3, "mutate": 3}
        self.probabilities = {"crossover": 0.5, "mutate": 0.5}

        # set from args
        self.__dict__.update(iterable, **kwargs)

        # how many CPU cores to use
        try:
            assert(self.n_core)
        except AssertionError:
            print("No CPU count (n_core) given. Using all cores.")
            self.n_core = cpu_count()
        if self.n_core == "max":
            self.n_core = cpu_count()

        # population size
        try:
            assert(self.population_size)
        except AssertionError:
            raise("No population size given")
        # number of generations to run
        try:
            assert(self.n_generation)
        except AssertionError:
            raise("Number of generations not set") # TODO stable gens?

        # compute absolute values for generation distribution
        self.generation = dict(zip(self.generation.keys(), [round(v*self.population_size / sum(self.generation.values())) for v in self.generation.values()]))
        try:
            assert(sum(self.generation.values()) == self.population_size)
        except AssertionError:
            raise("Strange population distribution given: {} does not add up to {}. Cannot continue.".format(self.generation, self.population_size))

        # attribute variation
        try:
            assert(self.attribute_variation)
        except AssertionError:
            raise("No attribute variation given")
        self.attribute_variation=[AttributeVariation(av) for av in self.attribute_variation]

        # oemof model to solve
        try:
            assert(self.model)
        except AssertionError:
            raise("No model given")

        # init deap
        creator.create("Fitness", base.Fitness, weights = self.weights)
        creator.create("Individual", list, fitness=creator.Fitness)
        self.tbx = base.Toolbox()

        # Define the population.
        self.tbx.register("individual", tools.initIterate, creator.Individual, self.initIndividual)
        self.tbx.register("select", tools.selBest)

        # Create a random initial population.
        self.population = [self.tbx.individual() for _ in range(self.population_size)]

    def initIndividual(self):
        # Callback function to create one individual with random genes
        return [randint(av.val_min, av.val_max) for av in self.attribute_variation]

    def fitness_function(self, index, individual, model):
        # compute fitness for individual
        # called async -> copies of individual and model given

        # update (copied) oemof model
        for i, av in enumerate(self.attribute_variation):
            model['components'][av.comp_name][av.comp_attribute] = individual[i]
        # generate awkward component array for use in smooth
        components = []
        for name, comp in model['components'].items():
            comp["name"] = name
            components.append(comp)
        model['components'] = components

        # Now that the model is updated according to the genes given by the GA, smooth can be run.
        try:
            smooth_result = run_smooth(model)
            # As a fitness value, give back the summed up total annuity (which will be minimized) [EUR/a].
            annuity_total = sum([c.results["annuity_total"] for c in smooth_result])
            individual.fitness.values = annuity_total, # has to be tuple
            individual.smooth_result = smooth_result

        except Exception as e:
            # The smooth run failed. Therefore the fitness value is set to infinity.
            print('Evaluation canceled ({})'.format(str(e)))

        return index, individual

    def err_callback(self, err_msg):
        # Async error callback
        print('Callback error at parallel computing! The error message is: {}'.format(err_msg))

    def set_fitness(self, result):
        # Async success calbback: update master individual
        self.population[result[0]] = result[1]

    def compute_fitness(self):
        # compute fitness of every individual in population
        # open worker n_core threads
        pool = Pool(processes = self.n_core)
        for idx, ind in enumerate(self.population):
            if not ind.fitness.valid:
                pool.apply_async(
                    self.fitness_function,
                    (idx, ind, self.model),
                    callback=self.set_fitness,
                    error_callback=self.err_callback
                )
        pool.close()
        pool.join()

    def run(self):
        seed() # init RNG

        print('\n+++++++ START GENETIC ALGORITHM +++++++')
        print('The optimization parameters chosen are:')
        print('  population_size: {}'.format(self.population_size))
        print('  distribution:    {}'.format(self.generation))
        print('  n_generation:    {}'.format(self.n_generation))
        print('  n_core:          {}'.format(self.n_core))
        print('+++++++++++++++++++++++++++++++++++++++\n')

        result = OptimizationResult()

        for gen in range(self.n_generation):
            # evaluate current population fitness
            self.compute_fitness()

            # compute multi-dimensional fitness value: sum of weighted dimensions
            fitnesses = [sum(v*w for v,w in zip(individual.fitness.values, self.weights)) for individual in self.population]

            # filter out individuals with invalid fitness values
            self.population = list(filter(lambda ind: ind[0].fitness.valid, zip(self.population, fitnesses)))

            if len(self.population) < self.generation["select"]:
                raise Exception("Not enough valid results found")

            # order by fitness
            self.population.sort(key=lambda ind: ind[1], reverse=False)

            # unzip population from fitness
            self.population, fitnesses = map(list, zip(*self.population))

            # update stats - count only valid
            result.stats.append({
                'i': gen,
                'mu': np.mean(fitnesses),
                'std': np.std(fitnesses),
                'max': np.max(fitnesses),
                'min': np.min(fitnesses)
            })

            # save latest best result
            result.best_smooth_result = self.population[0].smooth_result

            # crossover: get parents from best, select genes randomly
            offset = self.generation["select"]
            for i in range(self.generation["crossover"]):
                parent1 = self.tbx.clone(self.population[0])
                parent2 = self.tbx.clone(self.population[(i % self.generation["select"])+1]) # TODO: find more clever way of sampling parents
                child, _ = tools.cxUniform(parent1, parent2, indpb=self.probabilities["crossover"])
                del child.fitness.values # makes fitness invalid
                self.population[offset + i] = child

            # mutate: may change gene(s) within given range
            offset = offset + self.generation["crossover"]
            for i in range(self.generation["mutate"]):
                child = self.tbx.clone(self.population[i % self.generation["select"]])
                for j in range(len(child)):
                    if random() < self.probabilities["mutate"]:
                        child[j] = randint(self.attribute_variation[j].val_min, self.attribute_variation[j].val_max)
                    del child.fitness.values
                    self.population[offset + i] = child

            # print optimization progress info
            print('Iteration {}/{} finished. Best fit. val: {:.0f} Avg. fit. val: {:.0f}'.format(gen+1, self.n_generation, result.stats[-1]['min'], result.stats[-1]['mu']))

        # All generations computed
        # update result instance. Best in pop[0]
        # individuals_evaluated = population
        result.best_fit_val = self.population[0].fitness.values
        result.i_best_fit_val = 0
        result.best_gens = self.population[0]
        # best_smooth_result
        # stats is already set

        print('\n+++++++ GENETIC ALGORITHM FINISHED +++++++')
        print('The best individual is:')
        print('  fit_val: {}'.format(result.best_fit_val))
        for i, attr in enumerate(self.attribute_variation):
            print(' attribute {} - {} value: {}'.format(
                attr.comp_name, attr.comp_attribute, result.best_gens[i]))
        print('+++++++++++++++++++++++++++++++++++++++++++\n')

        return result

def run_optimization(opt_config, _model):
    # save GA params directly in config
    opt_config.update(opt_config.pop("ga_params", dict))
    # simplify oemof model: instead of components array, have dict with component names as key
    _names = [c.pop("name") for c in _model["components"]]
    _model.update({'components': dict(zip(_names, _model["components"]))})
    # save oemof model in config
    opt_config.update({"model": _model})
    # run GA
    return Optimization(opt_config).run()
