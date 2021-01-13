import smooth.optimization.run_optimization as opt

import pytest


class TestAV:
    # AttributeVariation
    def test_av(self):
        with pytest.raises(AssertionError):
            # no arguments
            opt.AttributeVariation()

        av = {}
        with pytest.raises(AssertionError):
            # empty dict
            opt.AttributeVariation(av)

        av = {
            "comp_name": "foo",
            "comp_attribute": "bar",
        }
        with pytest.raises(AssertionError):
            # value range missing
            opt.AttributeVariation(av)

        av["val_min"] = 0
        av["val_max"] = 5
        assert opt.AttributeVariation(av).val_step is None

        av["val_step"] = 0
        assert not hasattr(opt.AttributeVariation(av), "num_steps")

        av["val_step"] = 2
        assert opt.AttributeVariation(av).num_steps == 3  # 01, 23, 45

        av["val_step"] = 4
        assert opt.AttributeVariation(av).num_steps == 2  # 0123, 45


class TestIndividual:
    def test_individual(self):
        empty = opt.Individual([])
        assert len(empty) == 0

        values = [3, 1, 4]
        ind = opt.Individual(values)
        assert len(ind) == 3
        assert(ind.fitness) is None
        assert(ind.smooth_result) is None

        for i in range(len(values)):
            assert values[i] == ind[i]

        with pytest.raises(IndexError):
            # out of range
            ind[len(values)]

        assert(str(ind)) == str(values)

    def test_domination(self):
        i1 = opt.Individual([])
        i2 = opt.Individual([])

        # empty does not dominate
        assert not i1.dominates(i2)
        assert not i2.dominates(i1)

        # not dominate self
        assert not i1.dominates(i1)
        i1.fitness = [1, 1]
        assert not i1.dominates(i1)

        f = [-1, 0, 1]

        for i11 in range(len(f)):
            f11 = f[i11]
            for i12 in range(len(f)):
                f12 = f[i12]
                i1.fitness = [f11, f12]
                for i21 in range(len(f)):
                    f21 = f[i21]
                    for i22 in range(len(f)):
                        f22 = f[i22]
                        i2.fitness = [f21, f22]
                        if f11 > f21 and f12 >= f22:
                            assert i1.dominates(i2)
                        elif f11 >= f21 and f12 > f22:
                            assert i1.dominates(i2)
                        else:
                            assert not i1.dominates(i2)


class TestSort:
    def test_sort_by_values(self):
        assert len(opt.sort_by_values(0, [])) == 0
        assert len(opt.sort_by_values(1, [])) == 0
        assert len(opt.sort_by_values(0, [1])) == 0

        assert opt.sort_by_values(1, [1]) == [0]
        assert opt.sort_by_values(1, [1, 2, 3]) == [0]
        assert opt.sort_by_values(1, [2, 1, 3]) == [1]
        assert opt.sort_by_values(3, [1, 2, 3]) == [0, 1, 2]
        assert opt.sort_by_values(4, [1, 2, 3]) == [0, 1, 2]
        assert opt.sort_by_values(3, [3, 2, 1]) == [2, 1, 0]
        assert opt.sort_by_values(3, [2, 1, 3]) == [1, 0, 2]

    def test_fnds(self):
        assert opt.fast_non_dominated_sort([]) == [[]]

        i1 = opt.Individual([])
        i2 = opt.Individual([])
        # fitness None: no domination
        assert opt.fast_non_dominated_sort([i1, i2]) == [[0, 1]]

        i1.fitness = [0, 0]
        i2.fitness = [0, 0]
        # fitness equal: no domination
        assert opt.fast_non_dominated_sort([i1, i2]) == [[0, 1]]

        i2.fitness = [-1, 0]
        # i1 dominates i2
        assert opt.fast_non_dominated_sort([i1, i2]) == [[0], [1]]

        i2.fitness = [1, 0]
        # i2 dominates i1
        assert opt.fast_non_dominated_sort([i1, i2]) == [[1], [0]]

        i2.fitness = [-1, 1]
        # no domination
        assert opt.fast_non_dominated_sort([i1, i2]) == [[0, 1]]

    def test_cdf(self):
        assert len(opt.CDF([], [], 0)) == 0
        assert len(opt.CDF([], [], 1)) == 1
        assert len(opt.CDF([1], [], 0)) == 0
        assert len(opt.CDF([], [1], 0)) == 0
        assert len(opt.CDF([1], [1], 0)) == 0

        assert len(opt.CDF([1], [1], 1)) == 1
        assert len(opt.CDF([1], [1, 2], 1)) == 1
        assert len(opt.CDF([1], [1, 2], 2)) == 2
        assert len(opt.CDF([1, 2], [1, 2], 5)) == 5

        crowd = opt.CDF([0, 1, 2, 4], [0, 1, 2, 4], 4)  # inf, 1, 1.5, inf
        assert len(crowd) == 4
        # borders
        assert crowd[0] == crowd[3]
        assert crowd[0] > crowd[1]
        assert crowd[3] > crowd[2]
        # elements
        assert crowd[1] == 1
        assert crowd[2] == 1.5


class TestGA:

    av_dict = {
        "comp_name": "foo",
        "comp_attribute": "bar",
        "val_min": 0,
        "val_max": 10
    }

    def test_crossover(self):
        p1 = opt.Individual([1, 2, 3])
        p2 = opt.Individual([4, 5, 6])
        ch = opt.crossover(p1, p2)
        assert ch.fitness is None
        assert ch.smooth_result is None
        assert len(ch) == len(p1) and len(ch) == len(p2)
        for idx, gene in enumerate(ch):
            assert gene == p1[idx] or gene == p2[idx]

    def test_mutate(self):
        pa = opt.Individual([0, 4, 8])
        av = [opt.AttributeVariation(self.av_dict)]*len(pa)

        # basic tests
        ch = opt.mutate(pa, av)
        assert len(ch) == len(pa)
        assert ch.fitness is None
        assert ch.smooth_result is None

        # mutate without val_step
        for _ in range(10):
            ch = opt.mutate(pa, av)
            for gene in ch:
                assert gene >= 0 and gene <= 10

        # mutate with val_step
        for idx in range(len(av)):
            av[idx].val_step = 4
        for _ in range(10):
            ch = opt.mutate(pa, av)
            for gene in ch:
                assert gene == 0 or gene == 4 or gene == 8

    def test_fitness(self):
        idx = 1
        ind = opt.Individual([1])
        (idx2, ind2) = opt.fitness_function(idx, ind, None, [], None,
                                            ignore_zero=False, save_results=False)

        assert idx == idx2
        for gene_idx, gene in enumerate(ind):
            assert(gene) == ind2[gene_idx]
        # smooth throws error: no fitness or result
        assert ind2.fitness is None
        assert ind2.smooth_result is None

        # test ignore_zero
        ind = opt.Individual([0])
        model = {"components": {"foo": {"bar": 0}, "bar": {"foo": 0}}}
        av = [opt.AttributeVariation(self.av_dict)]
        opt.fitness_function(idx, ind, model, av, None, ignore_zero=False, save_results=False)
        assert {"foo", "bar"} == model["components"].keys()

        # ignore_zero: remove foo from model
        opt.fitness_function(idx, ind, model, av, None, ignore_zero=True, save_results=False)
        assert {"bar"} == model["components"].keys()

        # ignore_zero twice on same component
        model = {"components": {"foo": {"bar": 0}, "bar": {"foo": 0}}}
        ind = opt.Individual([0, 0])
        av = [opt.AttributeVariation(self.av_dict)]*2
        opt.fitness_function(idx, ind, model, av, None, ignore_zero=True, save_results=False)
        assert {"bar"} == model["components"].keys()

    def test_optimization(self):
        o = opt.Optimization({
            "population_size": 10,
            "n_generation": 1,
            "attribute_variation": [self.av_dict],
            "model": {None}
        })
        # smooth error: no result
        assert len(o.run()) == 0
