import os
import oemof.solph as solph
from smooth.components.component import Component
import smooth.framework.functions.functions as func


class EnergySourceFromCsv (Component):
    """ General energy sources are created through this class by importing csv files """

    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)

        """ PARAMETERS """
        self.name = 'General_energy_source'

        self.nominal_value = 1
        self.reference_value = 1
        self.csv_filename = None
        self.csv_separator = ';'
        self.column_title = 0
        self.path = os.path.dirname(__file__)
        self.bus_out = None

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

        """ READ CSV FILES """
        self.data = func.read_data_file(self.path, self.csv_filename,
                                        self.csv_separator, self.column_title)

        """ STATES """

    def create_oemof_model(self, busses, _):
        energy_source_from_csv = solph.Source(
            label=self.name,
            outputs={busses[self.bus_out]: solph.Flow(
                actual_value=self.data.iloc[self.sim_params.i_interval],
                nominal_value=self.nominal_value,
                fixed=True)})
        return energy_source_from_csv
