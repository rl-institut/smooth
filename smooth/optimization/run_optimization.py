"""This is the core of the genetic algorithm (GA) used for optimization.
It uses the `NSGA-II <https://www.sciencedirect.com/science/article/pii/S1877705811022466>`_
algorithm for multi-objective optimization of smooth components.

**********
How to use
**********
To use, call run_optimization with a configuration dictionary and your smooth model.
You will receive a list of :class:`Individual` in return. These individuals are
pareto-optimal in regard to the given objective functions (limited to two functions).

An example configuration can be seen in run_optimization_example in the
`examples directory <https://github.com/rl-institut/smooth/tree/dev/smooth/examples>`_.

Objective functions
-------------------
You may specify your custom objective functions for optimization.
These should be lambdas that take the result from run_smooth and return a value.
Keep in mind that this algorithm always tries to maximize.
In order to minimize a value, return the negative value.

Example 1: maximize *power_max* of the first component::

    lambda x: x[0].power_max

Example 2: minimize the annual costs::

    lambda x: -sum([component.results['annuity_total'] for component in x])

Result
------
After the given number of generations or aborting, the result is printed to the terminal.
All individuals currently on the pareto front are returned in a list.
Their `values` member contain the component attribute values in the order
given by the `attribute_variation` dictionary from the optimization params.
In addition, when `SAVE_ALL_SMOOTH_RESULTS` is set to True, the `smooth_result`
member of each individual contains the value returned by run_smooth.

.. warning::
    Using SAVE_ALL_SMOOTH_RESULTS and writing the result
    to a file will generally lead to a large file size.

**************
Implementation
**************
Like any GA, this implementation simulates a population which converges
to an optimal solution over multiple generations.
As there are multiple objectives, the solution takes the form of a pareto-front,
where no solution is dominated by another while maintaining distance to each other.
We take care to compute each individual configuration only once.
The normal phases of a GA still apply:

* selection
* crossover
* mutation

Population initialisation
-------------------------
At the start, a population is generated.
The size of the population must be declared (`population_size`).
Each component attribute to be varied in the smooth_model corresponds
to a gene in an individual. The genes are initialized randomly with a uniform
distribution between the minimum and maximum value of its component attribute.
These values may adhere to a step size (*val_step* in :class:`AttributeVariation`).

Selection
---------
We compute the fitness of all individuals in parallel.
You must set `n_core` to specify how many threads should be active at the same time.
This can be either a number or 'max' to use all virtual cores on your machine.
The fitness evaluation follows these steps:

#. change your smooth model according to the individual's component attribute values
#. run smooth
#. on success, compute the objective functions using the smooth result. \
These are the fitness values. On failure, print the error
#. update the master individual on the main thread with the fitness values
#. update the reference in the dictionary containing all evaluated individuals

After all individuals in the current generation have been evaluated,
they are sorted into tiers by NSGA-II fast non-dominated sorting algorithm.
Only individuals on the pareto front are retained,
depending on their distance to their neighbors.
The parent individuals stay in the population, so they can appear in the pareto front again.

Crossover
---------
These individuals form the base of the next generation, they are parents.
For each child in the next generation, genes from two randomly selected parents
are taken (uniform crossover of independent genes).

Mutation
--------
After crossover, each child has a random number of genes mutated.
The mutated value is around the original value, taken from a normal distribution.
Special care must be taken to stay within the component atrribute's range
and to adhere to a strict step size.

After crossover and mutation, we check that this individual's gene sequence
has not been encountered before (as this would not lead to new information
and waste computing time). Only then is it admitted into the new generation.

Special cases
-------------
We impose an upper limit of 1000 * `population_size` on the number of tries to
find new children. This counter is reset for each generation. If it is exceeded
and no new gene sequences have been found, the algorithm aborts and returns the current result.

In case no individuals have a valid smooth result, an entirely new population is generated.
No plot will be shown.
If only one individual is valid, the population is filled up with random individuals.

Gradient ascent
---------------
The solutions of the GA are pareto-optimal, but may not be at a local optimum.
Although new configurations to be evaluated are searched near the current ones,
it is not guaranteed to find slight improvements.
This is especially true if there are many dimensions to search
and the change is in only one dimension.
The chance to happen upon this single improvement is in
inverse proportion to the number of attribute variations.

Therefore, the *post_processing* option exists to follow the
fitness gradient for each solution after the GA has finished.
We assume that each attribute is independent of each other.
All solutions improve the same attribute at the same time.
The number of fitness evaluations may exceed the *population_size*,
however, the maximum number of cores used stays the same as before.

To find the local optimum of a single attribute of a solution,
we first have to find the gradient.
This is done by going one *val_step* in positive and negative direction.
These new children are then evaluated. Depending on the domination,
the gradient may be *+val_step*, -*val_step* or 0 (parent is optimal).
Then, this gradient is followed until the child shows no improvement.
The population may be topped up with multiples of *val_step*
to better utilize all cores and speed up the gradient ascent.
After all solutions have found their optimum for this attribute,
the next attribute is varied.

Plotting
--------
To visualize the current progress,
you can set the *plot_progress* simulation parameter to True.
This will show the current pareto front in a pyplot window.
You can mouse over the points to show the configuration and objective values.
To keep the computation running in the background (non-blocking plots)
while listening for user events, the plotting runs in its own process.

On initialisation, a one-directional pipe is established to send data
from the main computation to the plotting process.
The process is started right at the end of the initialisation.
It needs the attribute variations and objective names for hover info and axes labels.
It also generates a multiprocessing event which checks if the process shall be stopped.

In the main loop of the process, the pipe is checked for any new data.
This incorporates a timeout to avoid high processor usage.
If new data is available, the old plot is cleared
(along with any annotations, labels and titles) and redrawn from scratch.
In any case, the window listens for a short time for user input events like mouseover.
Window close is a special event which stops the process,
but not the computation (as this runs in the separate main process).

When hovering with the mouse pointer over a point in the pareto front,
an annotation is built with the info of the :class:`Individual`.
The annotation is removed when leaving the point. A simple example
of how this looks is illustrated in Figure 1. In this example,
after the first generation there is one optimal energy system
found which costs 244,416.21 EUR and produces 0 emissions.

.. figure:: /images/pareto_annotation.png
    :width: 60 %
    :alt: pareto_annotation.png
    :align: center

    Fig.1: Simple diagram of a pareto front with annotations

Sending None through the pipe makes the process show the plot until the user closes it.
This blocks the process, so no new data is received, but user events are still processed.
"""

import multiprocessing as mp
from tkinter import TclError     # plotting window closed
import random
import matplotlib.pyplot as plt  # only needed when plot_progress is set
import os                        # delete old result files
from datetime import datetime    # get timestamp for filename
import pickle                    # pickle intermediate results
import dill                      # dump objective functions

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
    :type val_min: number
    :param val_max: maximum value of component attribute (inclusive)
    :type val_max: number
    :param val_step: step size of component attribute
    :type val_step: number, optional
    :var num_steps: number of steps if *val_step* is set and not zero
    :type num_steps: int
    :raises: AssertionError when any non-optional parameter is missing or *val_step* is negative
    """

    def __init__(self, iterable=(), **kwargs):
        self.val_step = None
        self.__dict__.update(iterable, **kwargs)
        assert hasattr(self, "comp_name"), "comp_name missing"
        assert hasattr(self, "comp_attribute"), "{}: comp_attribute missing".format(self.comp_name)
        assert hasattr(
            self, "val_min"), "{} - {}: val_min missing".format(self.comp_name, self.comp_attribute)
        assert hasattr(
            self, "val_max"), "{} - {}: val_max missing".format(self.comp_name, self.comp_attribute)

        if self.val_step == 0:
            print("{} - {}: ignore val_step".format(self.comp_name, self.comp_attribute))
        if self.val_step:
            assert self.val_step >= 0, "{} - {}: val_step < 0".format(
                self.comp_name, self.comp_attribute)
            self.num_steps = int((self.val_max - self.val_min)/self.val_step) + 1


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
        return self.fitness is not None and (other.fitness is None or (
            (self.fitness[0] >= other.fitness[0] and self.fitness[1] > other.fitness[1]) or
            (self.fitness[0] > other.fitness[0] and self.fitness[1] >= other.fitness[1])))


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
    :return: indices of values sorted into their domination ranks (only first element used)
    :rtype: list of lists of indices
    """
    S = [[] for _ in p]  # which values dominate other?
    front = [[]]         # group values by number of dominations
    n = [0]*len(p)       # how many values does the value at this position dominate?
    # rank = [0]*len(p)    # rank within domination tree (unused)

    # compare all elements, see which ones dominate each other
    for i in range(0, len(p)):
        for j in range(0, len(p)):
            if p[i].dominates(p[j]) and j not in S[i]:
                S[i].append(j)
            elif p[j].dominates(p[i]):
                n[i] += 1
        if n[i] == 0:
            # element is not dominated: put in front
            # rank[i] = 0
            if i not in front[0]:
                front[0].append(i)

    i = 0
    while(len(front[i]) > 0):
        Q = []
        for p in front[i]:
            for q in S[p]:
                n[q] -= 1
                if n[q] == 0:
                    # rank[q] = i+1
                    if q not in Q:
                        Q.append(q)
        i = i+1
        front.append(Q)

    if len(front) > 1:
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

    if (n == 0 or len(values1) != n or len(values2) != n or
            max(values1) == min(values1) or max(values2) == min(values2)):
        return [1e100]*n

    distance = [0]*n
    sorted1 = sort_by_values(n, values1)
    sorted2 = sort_by_values(n, values2)
    distance[0] = 1e100  # border
    distance[-1] = 1e100
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
        # get new value within normal distribution around current value
        value = random.gauss(value, sigma)
        if attribute_variation[mut_gene_idx].val_step:
            # quantized value
            step = attribute_variation[mut_gene_idx].val_step
            value = round(delta_min / step) * step + val_min
        # clip value to bounds
        value = min(max(value, val_min), val_max)
        child[mut_gene_idx] = value
    return child


def fitness_function(
        index, individual,
        model,
        attribute_variation,
        dill_objectives,
        ignore_zero=False,
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
    :param ignore_zero: ignore components with an attribute value of zero
    :type ignore_zero: boolean
    :param save_results: save smooth result in individual?
    :type save_results: boolean
    :return: index, modified individual with fitness (None if failed)
        and smooth_result (none if not save_results) set
    :rtype: tuple(int, :class:`Individual`)
    """
    # update (copied) oemof model
    for i, av in enumerate(attribute_variation):
        if ignore_zero and individual[i] == 0:
            # remove component with zero value from model
            # use pop instead of del in case component is removed multiple times
            model['components'].pop(av.comp_name, None)
        else:
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


class PlottingProcess(mp.Process):
    """Process for plotting the intermediate results

    Data is sent through (onedirectional) pipe.
    It should be a dictionary containing "values" (array of :class:`Individual`)
    and "gen" (current generation number, displayed in title).
    Send None to stop listening for new data and block the Process by showing the plot.
    After the user closes the plot, the process returns and can be joined.

    :param pipe: data transfer channel
    :type pipe: `multiprocessing pipe \
<https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Pipe>`_
    :param attribute_variation: AV of :class:`Optimization`
    :type attribute_variation: list of :class:`AttributeVariation`
    :param objective_names: descriptive names of :class:`Optimization` objectives
    :type objective_names: list of strings
    :var exit_flag: Multiprocessing event signalling process should be stopped
    :var fig: figure for plotting
    :var ax: current graphic axis for plotting
    :var points: plotted results or None
    :var annot: current annotation or None
    """

    def __init__(self):
        self.exit_flag = mp.Event()
        self.exit_flag.clear()

    def main(self):
        """Main plotting thread

        Loops while exit_flag is not set and user has not closed window.
        Checks periodically for new data to be displayed.
        """

        # start of main loop: no results yet
        plt.title("Waiting for first results...")

        # loop until exit signal
        while not self.exit_flag.is_set():
            # poll with timeout (like time.sleep)
            while self.pipe.poll(0.1):
                # something in pipe
                data = self.pipe.recv()
                if data is None:
                    # special case
                    plt.title("Finished!")
                    # block process until user closes window
                    plt.show()
                    # exit process
                    return
                else:
                    # process sent data
                    # save sent results to show in annotation later
                    self.values = data["values"]
                    # use abs(r[]) to display positive values
                    f1_vals = [r.fitness[0] for r in data["values"]]
                    f2_vals = [r.fitness[1] for r in data["values"]]
                    # reset figure
                    self.ax.clear()
                    # redraw plot with new data
                    self.points, = self.ax.plot(f1_vals, f2_vals, '.b')
                    # new title and labels
                    plt.title(data.get("title", "Pareto front"), {'zorder': 1})
                    plt.xlabel(self.objective_names[0])
                    plt.ylabel(self.objective_names[1])
                    self.fig.canvas.draw()
            try:
                # redraw plot, capture events
                plt.pause(0.1)
            except TclError:
                # window may have been closed: exit process
                return
        # exit signal sent: stop process
        return

    def handle_close(self, event):
        """Called when user closes window

        Signal main loop that process should be stopped.
        """
        self.exit_flag.set()

    def hover(self, event):
        """Called when user hovers over plot.

        Checks if user hovers over point. If so, delete old annotation and
        create new one with relevant info from all Indivdiuals corresponding to this point.
        If user does not hover over point, remove annotation, if any.
        """
        if self.points and event.inaxes == self.ax:
            # results shown, mouse within plot: get event info
            # cont: any points hovered?
            # ind:  list of points hovered
            cont, ind = self.points.contains(event)

            if cont and "ind" in ind:
                ind = ind["ind"]
                # points hovered
                # get all point coordinates
                x, y = self.points.get_data()
                text = []
                for idx in ind:
                    # loop over points hovered
                    ind_text = ""
                    max_line_len = 0
                    # list all attribute variations with name and value
                    for av_idx, av in enumerate(self.attribute_variation):
                        line = "{}.{}: {}\n".format(
                            av.comp_name,
                            av.comp_attribute,
                            self.values[idx][av_idx])
                        ind_text += line
                        max_line_len = max(max_line_len, len(line))
                    # separator line
                    ind_text += '-'*max_line_len + "\n"
                    # list all objectives with name and value
                    for obj_idx, obj in enumerate(self.objective_names):
                        ind_text += "{}: {}\n".format(obj, self.values[idx].fitness[obj_idx])
                    text.append(ind_text)
                text = "\n".join(text)

                # remove old annotation
                if self.annot:
                    self.annot.remove()

                # create new annotation
                self.annot = self.ax.annotate(
                    text,
                    xy=(x[ind[0]], y[ind[0]]),
                    xytext=(-20, 20),
                    textcoords="offset points",
                    bbox=dict(boxstyle="round", fc="w"),
                    arrowprops={'arrowstyle': "-"},
                    annotation_clip=False)
                # self.annot.get_bbox_patch().set_alpha(0.4)
                self.fig.canvas.draw()
            elif self.annot and self.annot.get_visible():
                # no point hovered, but annotation present: remove annotation
                self.annot.remove()
                self.annot = None
                self.fig.canvas.draw()

    def __call__(self, pipe, attribute_variation, objective_names):
        """Process entry point.

        Set up plotting window, necessary variables and callbacks, call main loop.
        """
        self.pipe = pipe
        self.attribute_variation = attribute_variation
        self.objective_names = objective_names
        self.fig, self.ax = plt.subplots()
        self.points = None
        self.annot = None
        self.fig.canvas.mpl_connect('close_event', self.handle_close)
        self.fig.canvas.mpl_connect("motion_notify_event", self.hover)
        self.main()


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
    :param post_processing: improve GA solution with gradient ascent. Defaults to False
    :type post_processing: boolean, optional
    :param plot_progress: plot current pareto front. Defaults to False
    :type plot_progress: boolean, optional
    :param ignore_zero: ignore components with an attribute value of zero. Defaults to False
    :type ignore_zero: boolean, optional
    :param save_intermediate_results: write intermediate results to pickle file.
        Only the two most recent results are saved. Defaults to False
    :type save_intermediate_results: boolean, optional
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
        self.post_processing = False
        self.plot_progress = False
        self.ignore_zero = False
        self.save_intermediate_results = False
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
            self.n_core = mp.cpu_count()
        if self.n_core == "max":
            self.n_core = mp.cpu_count()

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
        self.evaluated = {}

        # save intermediate results?
        if self.save_intermediate_results:
            self.last_result_file_name = ""
            self.current_result_file_name = ""

        # plot intermediate results?
        if self.plot_progress:
            # set up plotting process with unidirectional pipe
            plot_pipe_rx, self.plot_pipe_tx = mp.Pipe(duplex=False)
            self.plot_process = mp.Process(
                target=PlottingProcess(),
                args=(plot_pipe_rx, self.attribute_variation, self.objective_names))
            self.plot_process.start()

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
        Remove invalid individuals from `population`
        """
        # open n_core worker threads
        pool = mp.Pool(processes=self.n_core)
        # set objective functions for each worker
        dill_objectives = dill.dumps(self.objectives)
        for idx, ind in enumerate(self.population):
            if ind.fitness is None:  # not evaluated yet
                pool.apply_async(
                    fitness_function,
                    (idx, ind, self.model, self.attribute_variation,
                        dill_objectives, self.ignore_zero, self.SAVE_ALL_SMOOTH_RESULTS),
                    callback=self.set_fitness,
                    error_callback=self.err_callback  # tb
                )
        pool.close()
        pool.join()

    def save_intermediate_result(self, result):
        """Dump result into pickle file in current working directory.
        Same content as smooth.save_results.
        The naming schema follows *date*-*time*-intermediate_result.pickle.
        Removes second-to-last pickle file from same run.

        :param result: the current results to be saved
        :type result: list of :class:`Individual`
        """

        # prepare file name by format
        filename_format = "%Y-%m-%d_%H-%M-%S_intermediate_result.pickle"
        new_result_file_name = datetime.now().strftime(filename_format)
        # write result to file
        with open(new_result_file_name, 'wb') as save_file:
            pickle.dump(result, save_file)
        # delete second-to-last result file (if not rewritten)
        if (os.path.exists(self.last_result_file_name)
                and self.last_result_file_name != self.current_result_file_name):
            os.remove(self.last_result_file_name)
        # update status
        self.last_result_file_name = self.current_result_file_name
        self.current_result_file_name = new_result_file_name
        print("Save intermediate results in {}".format(new_result_file_name))

    def gradient_ascent(self, result):
        """Try to fine-tune result(s) with gradient ascent

        Attributes are assumed to be independent and varied separately.
        Solutions with the same fitness are ignored.

        :param result: result from GA
        :type result: list of :class:`Individual`
        :return: improved result
        :rtype: list of :class:`Individual`
        """
        print('\n+++++++ Intermediate result +++++++')
        for i, v in enumerate(result):
            print(i, v.values, " -> ", dict(zip(self.objective_names, v.fitness)))
        print('+++++++++++++++++++++++++++++++++++\n')

        new_result = []
        # ignore solutions with identical fitness
        for i in range(len(result)):
            known_fitness = False
            for j in range(len(new_result)):
                known_fitness |= new_result[j].fitness == result[i].fitness
            if not known_fitness:
                new_result.append(result[i])

        num_results = len(new_result)

        for av_idx, av in enumerate(self.attribute_variation):
            # iterate attribute variations (assumed to be independent)
            print("Gradient descending {} / {}".format(av_idx+1, len(self.attribute_variation)))
            step_size = av.val_step or 1.0  # required for ascent
            self.population = []
            for i in range(num_results):
                # generate two children around parent to get gradient
                parent = new_result[i]
                # "below" parent, clip to minimum
                child1 = Individual([gene for gene in parent])
                child1[av_idx] = max(parent[av_idx] - step_size, av.val_min)
                child1_fingerprint = str(child1)
                # "above" parent, clip to maximum
                child2 = Individual([gene for gene in parent])
                child2[av_idx] = min(parent[av_idx] + step_size, av.val_max)
                child2_fingerprint = str(child2)
                # add to population. Take evaluated if exists
                try:
                    self.population.append(self.evaluated[child1_fingerprint])
                except KeyError:
                    self.population.append(child1)
                try:
                    self.population.append(self.evaluated[child2_fingerprint])
                except KeyError:
                    self.population.append(child2)

            # compute fitness of all new children
            # Keep invalid to preserve order (match parent to children)
            self.compute_fitness()

            # take note which direction is best for each individual
            # may be positive or negative step size or 0 (no fitness improvement)
            step = [0] * num_results
            for i in range(num_results):
                parent = new_result[i]
                child1 = self.population[2*i]
                child2 = self.population[2*i+1]
                # get domination within family
                if child1.dominates(parent):
                    if child2.dominates(child1):
                        # child 2 dominates
                        step[i] = step_size
                        new_result[i] = child2
                    else:
                        # child 1 dominates
                        step[i] = -step_size
                        new_result[i] = child1
                else:
                    # child1 does not dominate parent
                    if child2.dominates(parent):
                        # child 2 dominates
                        step[i] = step_size
                        new_result[i] = child2
                    else:
                        # parent is not dominated
                        step[i] = 0.0

            # continue gradient ascent of solutions until local optimum reached for all
            while sum(map(abs, step)) != 0.0:
                # still improvement: create new population
                self.population = []
                # dict for saving position of parent element
                reference = {}
                idx = 0

                # build new population
                # only parents with step != 0 (still changing)
                # each parent with step != 0 at least once
                # fill up to n_cores with multiples of steps
                # only non-evaluated configurations allowed
                while(len(self.population) < max(num_results, self.n_core)):
                    # position of parent element
                    pos = idx % num_results
                    # multiplier for step size (at least 1)
                    mult = (idx // num_results) + 1

                    if mult > 1 and len(self.population) >= self.n_core:
                        # population full
                        break

                    if idx > 1000 * num_results:
                        # avoid endless loop (no more valid entries?)
                        break

                    if step[pos]:
                        # result with step: generate child in step direction
                        parent = new_result[pos]
                        child = Individual([gene for gene in parent])
                        mul_step = step[pos] * mult
                        child[av_idx] = min(max(parent[av_idx] + mul_step, av.val_min), av.val_max)

                        fingerprint = str(child)
                        # avoid double computation
                        if fingerprint not in self.evaluated:
                            # child config not seen so far
                            self.population.append(child)
                            # block, so not in population again
                            self.evaluated[fingerprint] = None
                            # keep track of parent position
                            reference[len(self.population) - 1] = pos

                    idx += 1

                # compute fitness of all new children
                # Keep invalid to preserve order (match children to parent)
                self.compute_fitness()

                # check new dominance of parent and children
                # default: no improvement -> stop ascent of this attribute
                new_step = [0] * len(step)
                for idx, child in enumerate(self.population):
                    parent_idx = reference[idx]
                    parent = new_result[parent_idx]
                    if child.dominates(parent):
                        # domination continues: save child, keep base step
                        # this ensures a new generation
                        new_result[parent_idx] = child
                        new_step[parent_idx] = step[parent_idx]

                # update step sizes
                step = new_step

                # show current result in plot
                if self.plot_progress and self.plot_process.is_alive():
                    self.plot_pipe_tx.send({
                        'title': 'Gradient descending AV #{}'.format(av_idx+1),
                        'values': new_result
                    })

            # no more changes in any solution for this AV: give status update
            if self.save_intermediate_results:
                self.save_intermediate_result(new_result)

            # show current result in plot
            if self.plot_progress and self.plot_process.is_alive():
                self.plot_pipe_tx.send({
                    'title': 'Front after gradient descending AV #{}'.format(av_idx+1),
                    'values': new_result
                })

            # change next AV

        return new_result

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
            for tries in range(1000 * self.population_size):
                if (len(children) == self.population_size):
                    # population full (pop_size new individuals)
                    break

                # get random parents from pop_size best results
                try:
                    [parent1, parent2] = random.sample(self.population, 2)
                    # crossover and mutate parents
                    child = mutate(crossover(parent1, parent2), self.attribute_variation)
                except ValueError:
                    # not enough parents left / initial generation: generate random configuration
                    individual = []
                    for av in self.attribute_variation:
                        if av.val_step:
                            value = random.randrange(0, av.num_steps) * av.val_step + av.val_min
                        else:
                            value = random.uniform(av.val_min, av.val_max)
                        individual.append(value)
                    child = Individual(individual)

                # check if child configuration has been seen before
                fingerprint = str(child)
                if fingerprint not in self.evaluated:
                    # child config not seen so far
                    children.append(child)
                    # block, so not in population again
                    self.evaluated[fingerprint] = None
            else:
                print("Warning: number of retries exceeded. \
{} new configurations generated.".format(len(children)))

            if len(children) == 0:
                # no new children could be generated
                print("Aborting.")
                break

            # New population generated (parents + children)
            self.population += children

            # evaluate generated population
            self.compute_fitness()

            # filter out individuals with invalid fitness values
            self.population = list(
                filter(lambda ind: ind is not None and ind.fitness is not None, self.population))

            if len(self.population) == 0:
                # no configuration  was successful
                print("No individuals left. Building new population.")
                continue

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

            # save result to file
            if self.save_intermediate_results:
                self.save_intermediate_result(result)

            # show current pareto front in plot
            if self.plot_progress and self.plot_process.is_alive():
                self.plot_pipe_tx.send({
                    'title': 'Front for Generation #{}'.format(gen + 1),
                    'values': result
                })

            self.population = [self.population[i] for i in pop_idx]

            # next generation

        result.sort(key=lambda v: -v.fitness[0])

        if self.post_processing:
            result = self.gradient_ascent(result)

        print('\n+++++++ GENETIC ALGORITHM FINISHED +++++++')
        for i, attr in enumerate(self.attribute_variation):
            print(' {} - {}'.format(
                attr.comp_name, attr.comp_attribute))

        for i, v in enumerate(result):
            print(i, v.values, " -> ", dict(zip(self.objective_names, v.fitness)))
        print('+++++++++++++++++++++++++++++++++++++++++++\n')

        if self.plot_progress and self.plot_process.is_alive():
            self.plot_pipe_tx.send(None)    # stop drawing, show plot
            self.plot_process.join()        # wait until user closes plot

        # remove old intermediate results
        if self.save_intermediate_results:
            if os.path.exists(self.last_result_file_name):
                os.remove(self.last_result_file_name)
            if os.path.exists(self.current_result_file_name):
                os.remove(self.current_result_file_name)

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
