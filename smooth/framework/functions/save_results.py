import datetime
import pickle


def save_results(file_name, result_data):
    # Save the result of either a smooth run or an optimization run by the genetic algorithm.
    # Parameter:
    #  file_name: Name of the result pickle file [str].
    #  result_data: Data to save [?].

    # Create the name of result by using the current time and then "_smooth_optimization_result.pcl"
    time_now = datetime.datetime.now()
    file_name = time_now.strftime("%Y-%m-%d_%H-%M-%S") + "_{}.pickle".format(file_name)
    # Create pointer to the file where the result will be saved.
    save_file = open(file_name, 'wb')
    # Pickle the result.
    pickle.dump(result_data, save_file)
    save_file.close()
