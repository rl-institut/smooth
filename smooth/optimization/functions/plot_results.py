# PLOT RESULTS
def plot_optimization_results(optimization_results):
    # Plot the progress.
    import seaborn as sns
    import matplotlib.pyplot as plt

    stats = optimization_results.stats

    sns.set()

    # _ = plt.scatter(range(1, len(stats) + 1), [[s['mu'], s['min'], s['max']] for s in stats], marker='.')
    plt.plot([s['mu'] for s in stats], '.b')
    plt.plot([s['min'] for s in stats], '-g')

    _ = plt.title('average fitness per iteration')
    _ = plt.xlabel('generation')
    _ = plt.ylabel('fitness')

    plt.show()
