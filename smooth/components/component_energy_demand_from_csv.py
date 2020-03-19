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
        self.csv_separator = ','
        self.column_title = 0
        self.path = os.path.dirname(__file__)

        self.bus_in = None

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

        """ READ CSV FILES """
        self.data = func.read_data_file(self.path, self.csv_filename, self.csv_separator, self.column_title)

        """ STATES """

    def create_oemof_model(self, busses, _):
        energy_demand_from_csv = solph.Sink(
            label=self.name,
            inputs={busses[self.bus_in]: solph.Flow(
                actual_value=self.data.iloc[self.sim_params.i_interval],
                nominal_value=self.nominal_value,
                fixed=True)})
        return energy_demand_from_csv

