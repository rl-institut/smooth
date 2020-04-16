# PLOT RESULTS
def plot_optimization_results(optimization_results):
    # Plot the progress.
    import matplotlib.pyplot as plt

    stats = optimization_results.stats

    # _ = plt.scatter(
    #         range(1, len(stats) + 1),
    #         [[s['mu'], s['min'], s['max']] for s in stats],
    #         marker='.')

    plt.plot([s['mu'] for s in stats], '.b')
    plt.plot([s['min'] for s in stats], '-g')

    plt.title('average fitness per iteration')
    plt.xlabel('generation')
    plt.ylabel('fitness')

    # cmap = plt.cm.get_cmap("viridis")
    # cmap.set_bad(color="r")
    # plt.scatter(
    # [r[0] for r in result],
    # [r[1] for r in result],
    # c=[r[2] or float("inf") for r in result],
    # cmap=cmap,
    # plotnonfinite=True
    # )

    plt.show()
