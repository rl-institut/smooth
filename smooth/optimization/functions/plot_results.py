# PLOT RESULTS
def plot_optimization_results(optimization_results):
    # Plot the progress.
    import seaborn as sns
    import matplotlib.pyplot as plt

    stats = optimization_results.stats

    sns.set()

    _ = plt.scatter(range(1, len(stats) + 1), [s['mu'] for s in stats], marker='.')

    _ = plt.title('average fitness per iteration')
    _ = plt.xlabel('generation')
    _ = plt.ylabel('fitness')

    plt.show()
