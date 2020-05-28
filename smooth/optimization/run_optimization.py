from multiprocessing import Pool, cpu_count
import random
import matplotlib.pyplot as plt  # only needed when plot_progress is set
import dill

from smooth import run_smooth

# import traceback
# def tb(e):
# traceback.print_exception(type(e), e, e.__traceback__)


class AttributeVariation:
    """Class that contains all information about an attribute that is varied by the genetic algorithm

    :param comp_name: name of component that gets varied
    :type comp_name: string
    :param comp_attribute: component attribute that gets varied
    :type comp_attribute: string
    :param val_min: minimum value of component attribute
    :type val_min: int
    :param val_max: maximum value of component attribute (inklusive)
    :type val_max: int
    :param val_step: step size of component attribute. Defaults to 1
    :type val_step: int, optional
    :raises: AssertionError when any non-optional parameter is missing
    """
    def __init__(self, iterable=(), **kwargs):
        self.val_step = 1
        self.__dict__.update(iterable, **kwargs)
        assert hasattr(self, "comp_name"), "comp_name missing"
        assert hasattr(self, "comp_attribute"), "{}: comp_attribute missing".format(self.comp_name)
        assert hasattr(
            self, "val_min"), "{} - {}: val_min missing".format(self.comp_name, self.comp_attribute)
        assert hasattr(
            self, "val_max"), "{} - {}: val_max missing".format(self.comp_name, self.comp_attribute)


class Individual:
    """ Class for individuals evaluated by the genetic algorithm

    :param values: attribute values (individual configuration)
    :type values: list
    :var values: given values
    :var fitness: fitness values depending on objective functions
    :type fitness: tuple
    :var smooth_result: result from `run_smooth`
    """
    class IndividualIterator:
        """Class to iterate over gene values.

        """
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

    values = None           # list. Take care when copying.
    fitness = None          # tuple
    smooth_result = None    # result of run_smooth

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
        """Define dominance between individuals

        :param other: individual for comparison
        :type other: :class:`Individual`
        :return: True if both fitness values are greater or
            one is greater while the other is equal. False otherwise.
        :rtype: boolean
        """
        return (
            (self.fitness[0] > other.fitness[0] and self.fitness[1] > other.fitness[1]) or
            (self.fitness[0] >= other.fitness[0] and self.fitness[1] > other.fitness[1]) or
            (self.fitness[0] > other.fitness[0] and self.fitness[1] >= other.fitness[1]))


def sort_by_values(n, values):
    """Sort values

    :param values: values to sort
    :type values: iterable
    :param n: maximum number of returned values
    :type n: int
    :return: list of indices that correspond to the values sorted in ascending order, `n` maximum
    :rtype: list
    """
    return [i for e, i in sorted((e, i) for i, e in enumerate(values))][:n]


def fast_non_dominated_sort(p):
    """NSGA-II's fast non dominated sort

    :param p: values to sort
    :type p: iterable
    :return: indices of values sorted into their domination ranks
    :rtype: list of lists of indices
    """
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
    """Calculate crowding distance

    :param values1: values in first dimension
    :type values1: iterable
    :param values2: values in second dimension
    :type values2: iterable
    :param n: maximum number of values
    :type n: int
    :return: `n` crowding distance values
    :rtype: list
    """
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
    """Uniform crossover between two parents
        Selects random (independent) genes from one parent or the other

    :param parent1: First parent
    :type parent1: :class:`Individual`
    :param parent2: Second parent
    :type parent2: :class:`Individual`
    :return: Crossover between parents
    :rtype: :class:`Individual`
    """
    child = Individual([gene for gene in parent1])  # copy parent1
    for gene_idx, gene in enumerate(parent2):
        if random.random() < 0.5:
            child[gene_idx] = gene
    return child


def mutate(parent, attribute_variation):
    """Mutate a random number of parent genes around original value, within variation

    :param parent: parent individual
    :type parent: :class:`Individual`
    :param attribute_variation: AV for all genes in parent
    :type attribute_variation: list of :class:`AttributeVariation`
    :return: child with some parent genes randomly mutated
    :rtype: :class:`Individual`
    """
    # copy parent genes
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
    """Compute fitness for one individual
        Called async: copies of individual and model given

    :param index: index within population
    :type index: int
    :param individual: individual to evaluate
    :type individual: :class:`Individual`
    :param model: smooth model
    :type model: dict
    :param attribute_variation: attribute variations
    :type attribute_variation: list of :class:`AttributeVariation`
    :param dill_objectives: objective functions
    :type dill_objectives: tuple of lambda-functions pickled with dill
    :param save_results: save smooth result in individual?
    :type save_results: boolean
    :return: index, modified individual with fitness (None if failed)
        and smooth_result (none if not save_results) set
    :rtype: tuple(int, :class:`Individual`)
    """
    # update (copied) oemof model
    for i, av in enumerate(attribute_variation):
        model['components'][av.comp_name][av.comp_attribute] = individual[i]

    # Now that the model is updated according to the genes given by the GA, run smooth
    try:
        smooth_result = run_smooth(model)[0]
        individual.smooth_result = smooth_result if save_results else None
        # update fitness with given objective functions
        objectives = dill.loads(dill_objectives)
        individual.fitness = tuple(f(smooth_result) for f in objectives)

    except Exception as e:
        # The smooth run failed.The fitness score remains None.
        print('Evaluation canceled ({})'.format(str(e)))
    return index, individual


class Optimization:
    """Main optimization class to save GA parameters

    :param n_core: number of threads to use.
        May be 'max' to use all (virtual) cores
    :type n_core: int or 'max'
    :param n_generation: number of generation to run
    :type n_generation: int
    :param population_size: number of new children per generation.
        The actual size of the population may be higher -
        however, each individual is only evaluated once
    :type population_size: int
    :param attribute_variation: attribute variation information that will be used by the GA
    :type attribute_variation: list of dicts, see :class:`AttributeVariation`
    :param model: smooth model
    :type model: dict
    :param objectives: multi-objectives to optimize.
        These functions take the result from `run_smooth` and return a float.
        Positive sign maximizes, negative sign minimizes.
        Defaults to minimizing annual costs and emissions
    :type objectives: 2-tuple of lambda functions
    :param objective_names: descriptive names for optimization functions.
        Defaults to ('costs', 'emissions')
    :type objective_names: 2-tuple of strings, optional
    :param plot_progress: plot current pareto front. Defaults to False
    :type plot_progress: boolean, optional
    :param SAVE_ALL_SMOOTH_RESULTS: save return value of `run_smooth`
        for all evaluated individuals.
        **Warning!** When writing the result to file,
        this may greatly increase the file size. Defaults to False
    :type SAVE_ALL_SMOOTH_RESULTS: boolean, optional
    :var population: current individuals
    :type population: list of Individual
    :var evaluated: keeps track of evaluated individuals to avoid double computation
    :type evaluated: dict with fingerprint of individual->:class:`Individual`
    :var ax: current figure handle for plotting
    :type ax: pyplot Axes
    :raises: `AttributeError` or `AssertionError` when required argument is missing or wrong
    """

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

        # Init population with random values between attribute variation (val_max inclusive)
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
        """Async error callback

        :param err_msg: error message to print
        :type err_msg: string
        """
        print('Callback error at parallel computing! The error message is: {}'.format(err_msg))

    def set_fitness(self, result):
        """Async success callback
            Update master individual in population and `evaluated` dictionary

        :param result: result from fitness_function
        :type result: tuple(index, :class:`Individual`)
        """
        self.population[result[0]] = result[1]
        self.evaluated[str(result[1])] = result[1]

    def compute_fitness(self):
        """Compute fitness of every individual in `population` with `n_core` worker threads.
        Remove invalid indivuals from `population`
        """
        # open n_core worker threads
        pool = Pool(processes=self.n_core)
        # set objective functions for each worker
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
        """Main GA function

        :return: pareto-optimal configurations
        :rtype: list of :class:`Individual`
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
    """Entry point for genetic algorithm

    :param opt_config: Optimization parameters.
        May have separate `ga_params` dictionary or define parameters directly.
        See :class:`Optimization`.
    :type opt_config: dict
    :param _model: smooth model
    :type _model: dict or list (legacy)
    :return: pareto-optimal configurations
    :rtype: list of :class:`Individual`
    """
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
