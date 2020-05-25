from multiprocessing import Pool, cpu_count
import random
import matplotlib.pyplot as plt  # only needed when plot_progress is set
import dill

# import traceback
# def tb(e):
# traceback.print_exception(type(e), e, e.__traceback__)

from smooth import run_smooth


class AttributeVariation:
    # Class that contain all information about the attribute that is varied by
    # the genetic algorithm.
    # attributes: comp_name, comp_attribute, val_min, val_max
    # optional: val_step
    def __init__(self, iterable=(), **kwargs):
        self.val_step = None
        self.__dict__.update(iterable, **kwargs)
        assert hasattr(self, "comp_name"), "comp_name missing"
        assert hasattr(self, "comp_attribute"), "{}: comp_attribute missing".format(self.comp_name)
        assert hasattr(
            self, "val_min"), "{} - {}: val_min missing".format(self.comp_name, self.comp_attribute)
        assert hasattr(
            self, "val_max"), "{} - {}: val_max missing".format(self.comp_name, self.comp_attribute)


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

    values = None  # array. Take care when copying.
    fitness = None  # Tuple
    smooth_result = None  # result of run_smooth

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

    def dominates(self, other):
        return (
            (self.fitness[0] > other.fitness[0] and self.fitness[1] > other.fitness[1]) or
            (self.fitness[0] >= other.fitness[0] and self.fitness[1] > other.fitness[1]) or
            (self.fitness[0] > other.fitness[0] and self.fitness[1] >= other.fitness[1]))


def sort_by_values(n, values):
    # sort values, return list of indices with max size n
    return [i for e, i in sorted((e, i) for i, e in enumerate(values))][:n]


def fast_non_dominated_sort(p):
    # NSGA-II's fast non dominated sort
    S = [[]]*len(p)
    front = [[]]
    n = [0]*len(p)
    rank = [0]*len(p)

    # build domination tree
    for i in range(0, len(p)):
        for j in range(0, len(p)):
            if p[i].dominates(p[j]) and j not in S[i]:
                S[i].append(j)
            elif p[j].dominates(p[i]):
                n[i] += 1
        if n[i] == 0:
            rank[i] = 0
            if i not in front[0]:
                front[0].append(i)

    i = 0
    while(len(front[i]) > 0):
        Q = []
        for p in front[i]:
            for q in S[p]:
                n[q] -= 1
                if n[q] == 0:
                    rank[q] = i+1
                    if q not in Q:
                        Q.append(q)
        i = i+1
        front.append(Q)

    front.pop(len(front) - 1)
    return front


def CDF(values1, values2, n):
    # calculate crowding distance
    distance = [0]*n
    sorted1 = sort_by_values(n, values1)
    sorted2 = sort_by_values(n, values2)
    distance[0] = 1e100  # border
    distance[-1] = 1e100
    if max(values1) == min(values1) or max(values2) == min(values2):
        return [1e100]*n
    for k in range(1, n-1):
        distance[k] = distance[k] + (values1[sorted1[k+1]] -
                                     values2[sorted1[k-1]])/(max(values1)-min(values1))
    for k in range(1, n-1):
        distance[k] = distance[k] + (values1[sorted2[k+1]] -
                                     values2[sorted2[k-1]])/(max(values2)-min(values2))
    return distance


def crossover(parent1, parent2):
    # crossover between two parents
    # Selects random (independent) genes from one parent or the other
    child = Individual([gene for gene in parent1])  # copy parent1
    for gene_idx, gene in enumerate(parent2):
        if random.random() < 0.5:
            child[gene_idx] = gene
    return child


def mutate(parent, attribute_variation):
    # mutate parent
    # mutates a random number of genes around original value, within variation
    child = Individual([gene for gene in parent])
    # change between one and all genes of parent
    num_genes_to_change = random.randint(1, len(child))
    # get indices of genes to change
    genes_to_change = random.sample(range(len(child)), num_genes_to_change)
    for mut_gene_idx in genes_to_change:
        value = child[mut_gene_idx]
        # compute smallest distance to min/max of attribute
        val_min = attribute_variation[mut_gene_idx].val_min
        val_max = attribute_variation[mut_gene_idx].val_max
        delta_min = value - val_min
        delta_max = val_max - value
        delta = min(delta_min, delta_max)
        # sigma influences spread of random numbers
        # try to keep between min and max of attribute
        sigma = delta / 3 if delta > 0 else 1
        # get integer within normal distribution around current value
        value = random.gauss(value, sigma)
        if attribute_variation[mut_gene_idx].val_step:
            # quantized value
            step = attribute_variation[mut_gene_idx].val_step
            value = round(delta_min / step) * step + val_min
        # clip value to bounds
        value = int(min(max(value, val_min), val_max))
        child[mut_gene_idx] = value
    return child


def fitness_function(
        index, individual,
        model,
        attribute_variation,
        dill_objectives,
        save_results=False):
    # compute fitness for one individual
    # called async -> copies of individual and model given
    # program makes computer freeze when this is a class function?
    # update (copied) oemof model
    for i, av in enumerate(attribute_variation):
        model['components'][av.comp_name][av.comp_attribute] = individual[i]

    # Now that the model is updated according to the genes given by the GA, smooth can be run.
    try:
        smooth_result = run_smooth(model)[0]
        # SAVE_ALL_SMOOTH_RESULTS can be given as arg if necessary
        individual.smooth_result = smooth_result if save_results else None
        # update fitness with given objective functions
        objectives = dill.loads(dill_objectives)
        individual.fitness = tuple(f(smooth_result) for f in objectives)

    except Exception as e:
        # The smooth run failed.The fitness score remains None.
        print('Evaluation canceled ({})'.format(str(e)))
    return index, individual


class Optimization:

    def __init__(self, iterable=(), **kwargs):

        # set defaults
        self.plot_progress = False
        self.SAVE_ALL_SMOOTH_RESULTS = False

        # objective functions: tuple with lambdas
        # negative sign for minimizing
        # defaults to minimum of annual costs and emissions
        self.objectives = (
            lambda x: -sum([c.results["annuity_total"] for c in x]),
            lambda x: -sum([c.results["annual_total_emissions"] for c in x]),
        )
        # objective names for plotting
        self.objective_names = ('costs', 'emissions')

        # set parameters from args
        self.__dict__.update(iterable, **kwargs)

        # how many CPU cores to use
        try:
            assert(self.n_core)
        except (AssertionError, AttributeError):
            print("No CPU count (n_core) given. Using all cores.")
            self.n_core = cpu_count()
        if self.n_core == "max":
            self.n_core = cpu_count()

        # population size
        try:
            assert(self.population_size)
        except (AssertionError, AttributeError):
            raise AssertionError("No population size given")

        # number of generations to run
        # TODO run until no more change?
        try:
            assert(self.n_generation)
        except (AssertionError, AttributeError):
            raise AssertionError("Number of generations not set")

        # attribute variation
        try:
            assert(self.attribute_variation)
        except (AssertionError, AttributeError):
            raise AssertionError("No attribute variation given")
        self.attribute_variation = [AttributeVariation(av) for av in self.attribute_variation]

        # oemof model to solve
        try:
            assert(self.model)
        except (AssertionError, AttributeError):
            raise AssertionError("No model given.")

        # objectives
        assert len(self.objectives) == 2, "Need exactly two objective functions"
        assert len(self.objectives) == len(
            self.objective_names), "Objective names don't match objective functions"

        # Init population with random values between attribute variation
        self.population = []
        for _ in range(self.population_size):
            individual = []
            for av in self.attribute_variation:
                if av.val_step:
                    value = random.randrange(av.val_min, av.val_max+1, av.val_step)
                else:
                    value = random.randint(av.val_min, av.val_max)
                individual.append(value)
            self.population.append(Individual(individual))

        self.evaluated = {}

        # plot intermediate results?
        if self.plot_progress:
            self.ax = plt.figure().add_subplot(111)

    def err_callback(self, err_msg):
        # Async error callback
        print('Callback error at parallel computing! The error message is: {}'.format(err_msg))

    def set_fitness(self, result):
        # Async success callback: update master individual
        self.population[result[0]] = result[1]
        self.evaluated[str(result[1])] = result[1]

    def compute_fitness(self):
        # compute fitness of every individual in population
        # open worker n_core threads
        # set objective functions for each worker
        pool = Pool(processes=self.n_core)
        dill_objectives = dill.dumps(self.objectives)
        for idx, ind in enumerate(self.population):
            if ind.fitness is None:  # not evaluated yet
                pool.apply_async(
                    fitness_function,
                    (idx, ind, self.model, self.attribute_variation,
                     dill_objectives, self.SAVE_ALL_SMOOTH_RESULTS),
                    callback=self.set_fitness,
                    error_callback=self.err_callback  # tb
                )
        pool.close()
        pool.join()
        # filter out individuals with invalid fitness values
        self.population = list(
            filter(lambda ind: ind is not None and ind.fitness is not None, self.population))

    def run(self):
        """
        main GA function
        """
        random.seed()  # init RNG

        print('\n+++++++ START GENETIC ALGORITHM +++++++')
        print('The optimization parameters chosen are:')
        print('  population_size: {}'.format(self.population_size))
        print('  n_generation:    {}'.format(self.n_generation))
        print('  n_core:          {}'.format(self.n_core))
        print('+++++++++++++++++++++++++++++++++++++++\n')

        result = []

        for gen in range(self.n_generation):

            # generate offspring
            children = []

            # only children not seen before allowed in population
            # set upper bound for maximum number of generated children
            # population may not be pop_size big (invalid individuals)
            for tries in range(10 * self.population_size):
                if (len(children) == self.population_size) or gen == 0:
                    # population full (pop_size new individuals)
                    break

                # get random parents from pop_size best results
                try:
                    [parent1, parent2] = random.sample(self.population, 2)
                except ValueError:
                    break

                # crossover and mutate parents
                child = mutate(crossover(parent1, parent2), self.attribute_variation)

                # check if child configuration has been seen before
                fingerprint = str(child)
                if fingerprint not in self.evaluated:
                    # child config not seen so far
                    children.append(child)
                    # block, so not in population again
                    self.evaluated[fingerprint] = None

            if len(children) == 0 and gen > 0:
                # no new children could be generated
                print("Search room exhausted. Aborting.")
                break

            # New population generated (parents + children)
            self.population += children

            # evaluate generated population
            self.compute_fitness()

            if len(self.population) == 0:
                # no configuration  was successful
                print("No individuals left. Aborting.")
                break

            # sort population by fitness
            f1_vals2 = [i.fitness[0] for i in self.population]
            f2_vals2 = [i.fitness[1] for i in self.population]
            FNDS = fast_non_dominated_sort(self.population)
            CDF_values = [CDF(f1_vals2, f2_vals2, len(NDS)) for NDS in FNDS]

            # select individuals on pareto front, depending on fitness and distance
            pop_idx = []
            for i in range(0, len(FNDS)):
                FNDS2 = [FNDS[i].index(FNDS[i][j]) for j in range(0, len(FNDS[i]))]
                front22 = sort_by_values(len(FNDS2), CDF_values[i])
                front = [FNDS[i][front22[j]] for j in range(0, len(FNDS[i]))]
                front.reverse()
                pop_idx += [v for v in front[:self.population_size-len(pop_idx)]]
                if (len(pop_idx) == self.population_size):
                    break

            # save pareto front
            # values/fitness tuples for all non-dominated individuals
            result = [self.population[i] for i in FNDS[0]]

            # print info of current pareto front
            print("The best front for Generation # {} / {} is".format(
                gen+1, self.n_generation))
            for i, v in enumerate(FNDS[0]):
                print(i, self.population[v], self.population[v].fitness)
            print("\n")

            # show current pareto front in plot
            if self.plot_progress:
                # use abs(r[]) to display positive values
                f1_vals = [r.fitness[0] for r in result]
                f2_vals = [r.fitness[1] for r in result]
                self.ax.clear()
                self.ax.plot(f1_vals, f2_vals, '.b')
                plt.title('Front for Generation #{}'.format(gen+1))
                plt.xlabel(self.objective_names[0])
                plt.ylabel(self.objective_names[1])
                plt.draw()
                plt.pause(0.1)

            self.population = [self.population[i] for i in pop_idx]

            # next generation

        print('\n+++++++ GENETIC ALGORITHM FINISHED +++++++')
        for i, attr in enumerate(self.attribute_variation):
            print(' {} - {}'.format(
                attr.comp_name, attr.comp_attribute))
        result.sort(key=lambda v: -v.fitness[0])
        for i, v in enumerate(result):
            print(i, v.values, " -> ", dict(zip(self.objective_names, v.fitness)))
        print('+++++++++++++++++++++++++++++++++++++++++++\n')

        if self.plot_progress:
            plt.show()

        return result


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
