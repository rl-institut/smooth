from multiprocessing import Pool, cpu_count
import random
import matplotlib.pyplot as plt # only needed when plot_progress is set

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
    fitness = None # Tuple
    smooth_result = None # result of run_smooth

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

# sort values, return list of indices with max size n
def sort_by_values(n, values):
    return [i for e,i in sorted((e,i) for i,e in enumerate(values))][:n]

# NSGA-II's fast non dominated sort
def fast_non_dominated_sort(p):
    S = [[]]*len(p)
    front = [[]]
    n = [0]*len(p)
    rank = [0]*len(p)

    # build domination tree
    for i in range(0,len(p)):
        for j in range(0, len(p)):
            if p[i].dominates(p[j]) and j not in S[i]:
                S[i].append(j)
            elif p[j].dominates(p[i]):
                n[i] += 1
        if n[i]==0:
            rank[i] = 0
            if i not in front[0]:
                front[0].append(i)

    i = 0
    while(len(front[i]) > 0):
        Q=[]
        for p in front[i]:
            for q in S[p]:
                n[q] -= 1
                if n[q]==0:
                    rank[q]=i+1
                    if q not in Q:
                        Q.append(q)
        i = i+1
        front.append(Q)

    front.pop(len(front) - 1)
    return front

# calculate crowding distance
def CDF(values1, values2, n):
    distance = [0]*n
    sorted1 = sort_by_values(n, values1)
    sorted2 = sort_by_values(n, values2)
    distance[0] = 1e100 # border
    distance[-1] = 1e100
    if max(values1) == min(values1) or max(values2) == min(values2):
        return [1e100]*n
    for k in range(1,n-1):
        distance[k] = distance[k]+ (values1[sorted1[k+1]] - values2[sorted1[k-1]])/(max(values1)-min(values1))
    for k in range(1,n-1):
        distance[k] = distance[k]+ (values1[sorted2[k+1]] - values2[sorted2[k-1]])/(max(values2)-min(values2))
    return distance

# crossover between two parents
# Selects random (independent) genes from one parent or the other
def crossover(parent1, parent2):
    child = Individual([gene for gene in parent1]) # copy parent1
    for gene_idx, gene in enumerate(parent2):
        if random.random() < 0.5:
            child[gene_idx] = gene
    return child

# mutate parent
# mutates a random number of genes around original value, within variation
def mutate(parent, attribute_variation):
    child = Individual([gene for gene in parent])
    # change between one and all genes of parent
    num_genes_to_change = random.randint(1, len(child))
    # get indices of genes to change
    genes_to_change = random.sample(range(len(child)), num_genes_to_change)
    for mut_gene_idx in genes_to_change:
        # compute smallest distance to min/max of attribute
        val_min = attribute_variation[mut_gene_idx].val_min
        val_max = attribute_variation[mut_gene_idx].val_max
        delta_min = child[mut_gene_idx] - val_min
        delta_max = val_max - child[mut_gene_idx]
        delta = min(delta_min, delta_max)
        # sigma influences spread of random numbers
        # try to keep between min and max of attribute
        sigma = delta / 3 if delta > 0 else 1
        # mutate gene with normal distributaion around current value
        child[mut_gene_idx] = int(min(max(random.gauss(child[mut_gene_idx], sigma), val_min), val_max))
    return child

# compute fitness for one individual
# called async -> copies of individual and model given
# program makes computer freeze when this is a class function?
def fitness_function(index, individual, model, attribute_variation):
    # update (copied) oemof model
    for i, av in enumerate(attribute_variation):
        model['components'][av.comp_name][av.comp_attribute] = individual[i]

    # Now that the model is updated according to the genes given by the GA, smooth can be run.
    try:
        smooth_result = run_smooth(model)[0]
        # As first fitness value, compute summed up total annuity [EUR/a].
        annuity_total = -sum([c.results["annuity_total"] for c in smooth_result])
        # As second fitness value, compute emission [tons CO2/year]
        emission_total = -sum([c.results["annual_total_emissions"] for c in smooth_result])
        # compute overall fitness by multiplying with weight tuple
        # weight has negative sign to make positive numbers when minimizing
        individual.fitness = (annuity_total, emission_total)
        # individual.smooth_result = smooth_result if self.SAVE_ALL_SMOOTH_RESULTS else None

    except Exception as e:
        # The smooth run failed.The fitness score remains None.
        print('Evaluation canceled ({})'.format(str(e)))

    return index, individual

class Optimization:

    SAVE_ALL_SMOOTH_RESULTS = False

    def __init__(self, iterable=(), **kwargs):

        self.plot_progress = False

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
        self.evaluated = {}

        # plot intermediate results?
        if self.plot_progress:
            self.ax = plt.figure().add_subplot(111)

    def err_callback(self, err_msg):
        # Async error callback
        print('Callback error at parallel computing! The error message is: {}'.format(err_msg))

    def set_fitness(self, result):
        # Async success calbback: update master individual
        self.population[result[0]] = result[1]
        self.evaluated[str(self.population[result[0]])] = result[1]

    def compute_fitness(self):
        # compute fitness of every individual in population
        # open worker n_core threads
        pool = Pool(processes = self.n_core)
        for idx, ind in enumerate(self.population):
            if ind.fitness is None: # not evaluated yet
                pool.apply_async(
                    fitness_function,
                    (idx, ind, self.model, self.attribute_variation),
                    callback=self.set_fitness,
                    error_callback=self.err_callback #tb
                )
        pool.close()
        pool.join()
        # filter out individuals with invalid fitness values
        self.population = list(filter(lambda ind: ind is not None and ind.fitness is not None, self.population))

    def run(self):
        """
        main GA function
        """
        random.seed() # init RNG

        print('\n+++++++ START GENETIC ALGORITHM +++++++')
        print('The optimization parameters chosen are:')
        print('  population_size: {}'.format(self.population_size))
        print('  n_generation:    {}'.format(self.n_generation))
        print('  n_core:          {}'.format(self.n_core))
        print('+++++++++++++++++++++++++++++++++++++++\n')

        result = []

        for gen in range(self.n_generation):

            # evaluate current population fitness
            self.compute_fitness()
            if len(self.population) == 0:
                print("No individuals left. Aborting.")
                break

            FNDS = fast_non_dominated_sort(self.population)
            # save pareto front
            result = [(self.population[i].values, self.population[i].fitness) for i in FNDS[0]]

            # print info of current pareto front
            print("The best front for Generation number {} / {} is".format(gen+1, self.n_generation))
            for i,v in enumerate(FNDS[0]):
                print(i, self.population[v], self.population[v].fitness)
            print("\n")

            # show current pareto front in plot
            if self.plot_progress:
                f1_vals = [-i.fitness[0] for i in self.population]
                f2_vals = [-i.fitness[1] for i in self.population]
                self.ax.clear()
                self.ax.plot(f1_vals, f2_vals, '.b')
                plt.title('Front for Generation #{}'.format(gen+1))
                plt.xlabel('costs')
                plt.ylabel('emissions')
                plt.draw()
                plt.pause(0.1)

            population2 = self.population
            # generate offspring
            tries = 0
            while(len(population2)!=2*self.population_size):
                [parent1, parent2] = random.sample(self.population,2)
                child = mutate(crossover(parent1, parent2), self.attribute_variation)
                fingerprint = str(child)
                tries += 1
                if fingerprint not in self.evaluated:
                    # child config not seen so far
                    population2.append(child)
                    # block, so not in population again
                    self.evaluated[fingerprint] = None
                if tries > 1000 * self.population_size:
                    print("Search room exhausted. Aborting.")
                    break
            else:
                # New population successfully generated.
                # evaluate generated population
                self.population = population2
                self.compute_fitness()
                if len(self.population) == 0:
                    print("No individuals left. Aborting.")
                    break

                f1_vals2 = [i.fitness[0] for i in self.population]
                f2_vals2 = [i.fitness[1] for i in self.population]
                FNDS2 = fast_non_dominated_sort(self.population)
                CDF_values = [CDF(f1_vals2,f2_vals2,len(NDS)) for NDS in FNDS2]

                # select individuals on pareto front, depending on fitness and distance
                pop_idx = []
                for i in range(0,len(FNDS2)):
                    FNDS2_1 = [FNDS2[i].index(FNDS2[i][j]) for j in range(0, len(FNDS2[i]))]
                    front22 = sort_by_values(len(FNDS2_1), CDF_values[i])
                    front = [FNDS2[i][front22[j]] for j in range(0,len(FNDS2[i]))]
                    front.reverse()
                    pop_idx += [v for v in front[:self.population_size-len(pop_idx)]]
                    if (len(pop_idx) == self.population_size):
                        break
                self.population = [self.population[i] for i in pop_idx]

                continue
            # generation broke off: stop GA
            break

        print('\n+++++++ GENETIC ALGORITHM FINISHED +++++++')
        for i, attr in enumerate(self.attribute_variation):
            print(' {} - {}'.format(
                attr.comp_name, attr.comp_attribute))
        for i,v in enumerate(result):
            print(i, v[0], " -> ", v[1])
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
