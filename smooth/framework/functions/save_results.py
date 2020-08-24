import datetime
import pickle


def save_results(file_name, result_data):
    """Save the result of either a smooth run or an optimization run by the genetic algorithm.

    :param file_name: name of the result pickle file
    :type file_name: string
    :param result_data: data to save
    """

    # Create the name of result by using the current time and then "_smooth_optimization_result.pcl"
    time_now = datetime.datetime.now()
    file_name = time_now.strftime("%Y-%m-%d_%H-%M-%S_{}.pickle".format(file_name))
    # Create pointer to the file where the result will be saved.
    with open(file_name, 'wb') as save_file:
        # Pickle the result.
        pickle.dump(result_data, save_file)
