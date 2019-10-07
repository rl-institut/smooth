import smooth.framework.functions.functions as func

class SimulationParameters:

    def __init__(self, params):

        """ PARAMETERS """
        self.start_date = '1/1/2019'
        self.frequency = 'H'
        self.n_intervals = 24*7
        # Interval time [min].
        self.interval_time = 60

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

        self.date_time_index = func.set_date_time_index(self.start_date, self.n_intervals - 1, self.frequency)

    def set_parameters(self, params):
        for this_param in params:
            if not hasattr(self, this_param):
                raise ValueError('The parameter "{}" is not part of the simulation parameters'.format(this_param))

            setattr(self, this_param, params[this_param])













