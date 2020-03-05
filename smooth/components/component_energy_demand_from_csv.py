import os
import oemof.solph as solph
from smooth.components.component import Component
import smooth.framework.functions.functions as func
import numpy as np
import pandas as pd


class EnergyDemandFromCsv(Component):
    """ Energy demand created through this class from a csv file """

    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)
        """ PARAMETERS """
        self.name = 'Demand_default_name'

        self.nominal_value = 1
        self.csv_filename = None
        self.csv_filename_2 = None
        self.csv_separator = ','
        self.csv_separator_2 = ';'
        self.column_title = 0
        self.column_title_2 = 0
        self.path = os.path.dirname(__file__)

        self.bus_in = None

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

        """ READ CSV FILES """
        self.data = func.read_data_file(self.path, self.csv_filename, self.csv_separator, self.column_title)
        self.data_2 = func.read_data_file(self.path, self.csv_filename_2, self.csv_separator_2, self.column_title_2)

        self.data_year = pd.concat([self.data]*52, ignore_index=True)
        self.data_year_2 = pd.concat([self.data_2]*52, ignore_index=True)

        self.data_new = self.data_year.div(self.data_year_2)
        self.data_new = self.data_new.replace(np.nan, 0)

        """ STATES """

    def create_oemof_model(self, busses, _):
        energy_demand_from_csv = solph.Sink(
            label=self.name,
            inputs={busses[self.bus_in]: solph.Flow(
                actual_value=self.data_new.iloc[self.sim_params.i_interval],
                nominal_value=self.nominal_value,
                fixed=True)})
        return energy_demand_from_csv

