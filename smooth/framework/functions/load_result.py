import pickle

def load_result(file_path):
    # Load the result of either a smooth run or an optimization run by the genetic algorithm.
    # Parameter:
    #  file_path: Path of the result pickle file [str].

    # Create a pointer to the file.
    file_to_load = open(file_path, 'rb')
    # Return the results.
    return pickle.load(file_to_load)
