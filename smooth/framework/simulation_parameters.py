import smooth.framework.functions.functions as func


class SimulationParameters:
    """Class to store parameters for smooth simulation.

    :param start_date: the first evaluated time period. Defaults to '1/1/2019'
    :type start_date: string representation of date
    :param n_intervals: number of time steps. Defaults to 24*7=168
    :type n_intervals: integer
    :param interval_time: length of one time step in minutes. Defaults to 60 (one hour)
    :type interval_time: integer
    :param interest_rate: Interest rate for calculating annuity out of CAPEX. Defaults to 0.03 (3%)
    :type interest_rate: float
    :param print_progress: Decide if the running progress should be printed out. Defaults to False
    :type print_progress: boolean
    :param show_debug_flag: Decide if last result values should be shown
        in case solver was not successful. Defaults to True
    :type show_debug_flag: boolean
    :var date_time_index: pandas date range of all time periods to be evaluated
    :var sim_time_span: length of simulation time range in minutes
    """

    def __init__(self, params):
        # ------------------- PARAMETERS -------------------
        self.start_date = '1/1/2019'
        self.n_intervals = 24*7
        self.interval_time = 60
        self.interest_rate = 0.03
        self.print_progress = False
        self.show_debug_flag = True

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)

        # Date time index.
        self.date_time_index = func.get_date_time_index(
            self.start_date, self.n_intervals, self.interval_time)
        # Time span of the simulation [min].
        self.sim_time_span = func.get_sim_time_span(self.n_intervals, self.interval_time)

    def set_parameters(self, params):
        """Helper function to set simulation parameters on initialisation.

        :param params: parameters to set
        :type params: dictionary
        :raises: *ValueError* for unsupported simulation parameters
        """
        for this_param in params:
            if not hasattr(self, this_param):
                raise ValueError(
                    'The parameter "{}" is not part of the simulation parameters'
                    .format(this_param))

            setattr(self, this_param, params[this_param])
