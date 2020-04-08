from multiprocessing import Pool, cpu_count
import random
import numpy as np

# import traceback
# def tb(e):
    # traceback.print_exception(type(e), e, e.__traceback__)

from smooth import run_smooth

class AttributeVariation:
    # Class that contain all information about the attribute that is varied by the genetic algorithm.
    # recommended attributes: comp_name, comp_attribute, val_min, val_max
    def __init__(self, iterable=(), **kwargs):
        self.__dict__.update(iterable, **kwargs)

class Individual:
    class IndividualIterator:
        # Class to iterate over gene values
        def __init__(self, individual):
            self._idx = 0
            self.individual = individual
        def __next__(self):
            try:
                return self.individual.values[self._idx]
            except IndexError:
                raise StopIteration
            finally:
                self._idx += 1

    values  = None # array. Take care when copying.
    fitness = None # Single value
    smooth_value = None # result of run_smooth

    def __init__(self, values):
        self.values = values
    def __str__(self):
        return str(self.values)

    # enable iteration over values
    def __iter__(self):
        return self.IndividualIterator(self)
    def __len__(self):
        return len(self.values)

    # access values directly
    def __getitem__(self, idx):
        return self.values[idx]
    def __setitem__(self, idx, value):
        self.values[idx] = value

class OptimizationResult:
    # Class to store result from GA
    individuals_evaluated = dict()
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

        # weights: tuple controlling fitness function of optimization.
        # negative numbers minimize, the absolute value describes relative importance.
        # First value is linked to cost, the second to emissions.
        # (-1, -1) means minimze costs and emissions, with equal importance.
        self.weights = (-1.0, -1.0)

        # generation: dictionary with relative number of individuals to select, crossover and mutate in each generation.
        # With a population_size of 30, a 2/3/5 generation:
        # - selects 6 best individuals without change
        # - generates at most 9 children through crossover of these 6 selected
        # - generates at least 15 children through mutation of the 6 selected
        self.generation = {"select": 2, "crossover": 3, "mutate": 5}

        # probability for change
        # crossover change determines how likely a gene from
        # the second parent is picked instead of the first
        self.probabilities = {"crossover": 0.5}

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
        # May not fit completely (rounding), but upper limit anyway
        # During execution, mutation might occur more often
        self.generation = dict(zip(self.generation.keys(), [round(v*self.population_size / sum(self.generation.values())) for v in self.generation.values()]))

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

        # Init population with random values between attribute variation
        self.population = [Individual(
            [random.randint(av.val_min, av.val_max) for av in self.attribute_variation])
        for _ in range(self.population_size)]

    def fitness_function(self, index, individual, model):
        # compute fitness for individual
        # called async -> copies of individual and model given

        # update (copied) oemof model
        for i, av in enumerate(self.attribute_variation):
            model['components'][av.comp_name][av.comp_attribute] = individual[i]

        # Now that the model is updated according to the genes given by the GA, smooth can be run.
        try:
            smooth_result = run_smooth(model)[0]
            # As first fitness value, compute summed up total annuity [EUR/a].
            annuity_total = sum([c.results["annuity_total"] for c in smooth_result])
            # As second fitness value, compute emission [tons CO2/year]
            emission_total = sum([c.results["annual_total_emissions"] for c in smooth_result])
            # compute overall fitness by multiplying with weight tuple
            # weight has negative sign to make positive numbers when minimizing
            values = (annuity_total, emission_total)
            individual.fitness = sum(-w*v for v,w in zip(values, self.weights))
            individual.smooth_result = smooth_result if self.SAVE_ALL_SMOOTH_RESULTS else None

        except Exception as e:
            # The smooth run failed.The fitness score remains None.
            print('Evaluation canceled ({})'.format(str(e)))

        return index, individual #.fitness

    def err_callback(self, err_msg):
        # Async error callback
        print('Callback error at parallel computing! The error message is: {}'.format(err_msg))

    def set_fitness(self, result):
        # Async success calbback: update master individual
        self.population[result[0]] = result[1]
        # self.result.individuals_evaluated[str(self.population[result[0]])].fitness = result[1] # no join?
        self.result.individuals_evaluated[str(self.population[result[0]])] = result[1]

    def compute_fitness(self):
        # compute fitness of every individual in population
        # open worker n_core threads
        pool = Pool(processes = self.n_core)
        for idx, ind in enumerate(self.population):
            if ind.fitness is None: # not evaluated yet
                pool.apply_async(
                    self.fitness_function,
                    (idx, ind, self.model),
                    callback=self.set_fitness,
                    error_callback=self.err_callback #tb
                )
        pool.close()
        pool.join()

    def weights_to_str(self):
        # prepare human readable string describing weights (min/max/ignore)
        dims = ["costs", "emissions"]
        strings = [("minimize " if w < 0
                else "ignore " if w == 0
                else "maximize "
        ) + d for (d,w) in zip(dims, self.weights)]
        return ", ".join(strings)

    def run(self):
        """
        main GA function
        In each timestep/generation:
        - filter out bad results
        - select best
        - crossover those with each other
        - mutate best individuals

        Stop after set amount of generations or if no new individuals could be generated
        Therefore, we need to keep track which configurations have been tested so far.
        """
        random.seed() # init RNG

        print('\n+++++++ START GENETIC ALGORITHM +++++++')
        print('The optimization parameters chosen are:')
        print('  population_size: {}'.format(self.population_size))
        print('  distribution:    {}'.format(self.generation))
        print('  n_generation:    {}'.format(self.n_generation))
        print('  n_core:          {}'.format(self.n_core))
        print('  {}'.format(self.weights_to_str()))
        print('+++++++++++++++++++++++++++++++++++++++\n')

        self.result = OptimizationResult()

        for gen in range(self.n_generation):
            # evaluate current population fitness
            self.compute_fitness()

            # filter out individuals with invalid fitness values
            self.population = list(filter(lambda ind: ind is not None and ind.fitness is not None, self.population))

            # too many invalid?
            if len(self.population) < self.generation["select"]:
                raise Exception("Not enough valid results found")

            # order by fitness (ascending: minimize)
            self.population.sort(key=lambda ind: ind.fitness, reverse=False)

            # save latest best result
            self.result.best_smooth_result = self.population[0].smooth_result

            fitnesses = [ind.fitness for ind in self.population] # abs values?

            # update stats - count only valid
            self.result.stats.append({
                'i': gen,
                'mu':  np.mean(fitnesses),
                'std': np.std(fitnesses),
                'max': np.max(fitnesses),
                'min': np.min(fitnesses)
            })

            select_population = self.population[:self.generation["select"]]
            self.population = select_population

            # crossover: get parents from best, select genes randomly
            if len(select_population) > 1:
                for _ in range(self.generation["crossover"]):
                    # select two parents
                    [parent1, parent2] = random.sample(select_population, 2)
                    child = Individual([p for p in parent1.values]) # copy values
                    # switch genes randomly
                    for gene_idx, gene in enumerate(parent2):
                        # switch based on probability
                        if random.random() < self.probabilities["crossover"]:
                            child[gene_idx] = gene
                    fingerprint = str(child)
                    if fingerprint not in self.result.individuals_evaluated:
                        # child config not seen so far
                        self.population.append(child)
                        self.result.individuals_evaluated[fingerprint] = None # block, so not in population again

            # mutate: may change gene(s) within given range
            tries = 0 # count how often new configs were created this generation
            while len(self.population) < self.population_size:
                # population not full yet
                # select parent from most fit
                parent = random.choice(select_population)
                child = Individual([p for p in parent.values]) # copy values
                tries += 1

                # change between one and all genes of parent
                num_genes_to_change = random.randint(1, len(child))
                # get indices of genes to change
                genes_to_change = random.sample(range(len(child)), num_genes_to_change)
                for mut_gene_idx in genes_to_change:
                    # compute smallest distance to min/max of attribute
                    val_min = self.attribute_variation[mut_gene_idx].val_min
                    val_max = self.attribute_variation[mut_gene_idx].val_max
                    delta_min = child[mut_gene_idx] - val_min
                    delta_max = val_max - child[mut_gene_idx]
                    delta = min(delta_min, delta_max)
                    # sigma influences spread of random numbers
                    # higher generations have less spread
                    # try to keep between min and max of attribute
                    sigma = delta / (3 / (gen + 1)) if delta > 0 else 1
                    # mutate gene with normal distributaion around current value
                    child[mut_gene_idx] = int(min(max(random.gauss(child[mut_gene_idx], sigma), val_min), val_max))

                fingerprint = str(child)
                if fingerprint not in self.result.individuals_evaluated:
                    # child configuration not seen so far
                    self.population.append(child)
                    self.result.individuals_evaluated[fingerprint] = None # block, so not in population again
                if tries > 1000 * self.population_size:
                    print("Search room exhausted. Aborting.")
                    break
            else:
                # New population successfully generated.
                # Print info
                print('Iteration {}/{} finished. Best fit. val: {:.0f} Avg. fit. val: {:.0f}'.format(gen+1, self.n_generation, self.result.stats[-1]['min'], self.result.stats[-1]['mu']))
                continue
            # mutation broke off: stop GA
            break

        # All generations computed
        # update result instance. Best in pop[0]
        self.result.best_fit_val = self.population[0].fitness
        self.result.i_best_fit_val = 0
        self.result.best_gens = self.population[0]
        # stats is already set

        print('\n+++++++ GENETIC ALGORITHM FINISHED +++++++')
        print('The best individual is:')
        print('  fit_val: {}'.format(self.result.best_fit_val))
        for i, attr in enumerate(self.attribute_variation):
            print(' attribute {} - {} value: {}'.format(
                attr.comp_name, attr.comp_attribute, self.result.best_gens[i]))
        print('+++++++++++++++++++++++++++++++++++++++++++\n')

        # print all generated configuartions, ordered by fitness
        # pop = [(k, int(v.fitness)) for k,v in filter(lambda t: t[1] is not None and t[1].fitness is not None, self.result.individuals_evaluated.items())]
        # pop.sort(key=lambda t: t[1])
        # print(pop)

        return self.result

def run_optimization(opt_config, _model):
    # save GA params directly in config
    opt_config.update(opt_config.pop("ga_params", dict))
    if isinstance(_model["components"], list):
        # simplify oemof model: instead of components array, have dict with component names as key
        _names = [c.pop("name") for c in _model["components"]]
        _model.update({'components': dict(zip(_names, _model["components"]))})
    # save oemof model in config
    opt_config.update({"model": _model})
    # run GA
    return Optimization(opt_config).run()
