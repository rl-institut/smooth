import smooth.framework.functions.functions as func


class SimulationParameters:

    def __init__(self, params):

        """ PARAMETERS """
        self.start_date = '1/1/2019'
        self.n_intervals = 24*7
        # Interval time [min].
        self.interval_time = 60
        # Interest rate for calculating annuity out of CAPEX (e.g. 0.03 --> 3 %) [-].
        self.interest_rate = 0.03
        # Decide if the running progress should be printed out.
        self.print_progress = False
        # Decide if last result values should be shown in case solver was not successful
        self.show_debug_flag = True

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

        # Date time index.
        self.date_time_index = func.get_date_time_index(self.start_date, self.n_intervals, self.interval_time)
        # Time span of the simulation [min].
        self.sim_time_span = func.get_sim_time_span(self.n_intervals, self.interval_time)

    def set_parameters(self, params):
        for this_param in params:
            if not hasattr(self, this_param):
                raise ValueError('The parameter "{}" is not part of the simulation parameters'.format(this_param))

            setattr(self, this_param, params[this_param])













