import pickle


def load_results(file_path):
    """Load the result of either a smooth run or an optimization run by the genetic algorithm.

    :param file_path: path of the result pickle file
    :type file_path: string
    """
    with open(file_path, 'rb') as file_to_load:
        return pickle.load(file_to_load)
