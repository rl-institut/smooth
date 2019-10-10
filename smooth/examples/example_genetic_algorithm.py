import random
from smooth.examples.example_electrolyzer import mymodel
from smooth.framework.run import run
from deap import creator, base, tools, algorithms

# Creating a fitness object, while negative weights lead to a minimization problem.
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
# Setting up first individual.
creator.create("Individual", list, fitness=creator.FitnessMin)

toolbox = base.Toolbox()
# REGISTER - links function (2nd input) to alias (1st input). Other input goes into the linked function (2nd input).
# Redirect the random function to the alias attr_float
toolbox.register("attr_float", random.randint, 0, 1)
pop_size = 20
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_float, n=pop_size)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)


def evalOneMax(individual):
    return sum(individual),


def change_comp_value(components, comp_name, val_name, new_val):
    # Change the value val_name of one of the components (defined by comp_name) to new_val.
    for this_comp in components:
        if this_comp.name == comp_name:
            setattr(this_comp, val_name, new_val)


def fitness_function(individual):
    # Adjust the components according to the individuals.
    change_comp_value(mymodel['components'], 'this_ely', individual[0])
    # run the simulation
    components = run(mymodel)
    # Calculate the fitness value total annuity [EUR/a].
    annuity_of_all_components = 0
    for this_component in components:
        annuity_of_all_components += this_component.results['annuity_total']

    return  annuity_of_all_components


toolbox.register("evaluate", evalOneMax)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
toolbox.register("select", tools.selTournament, tournsize=3)

population = toolbox.population(n=300)

NGEN=40
for gen in range(NGEN):
    offspring = algorithms.varAnd(population, toolbox, cxpb=0.5, mutpb=0.1)
    fits = toolbox.map(toolbox.evaluate, offspring)
    for fit, ind in zip(fits, offspring):
        ind.fitness.values = fit
    population = toolbox.select(offspring, k=len(population))
top10 = tools.selBest(population, k=10)