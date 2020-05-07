import os
import oemof.solph as solph
from smooth.components.component import Component
import smooth.framework.functions.functions as func


class EnergyDemandFromCsv(Component):
    """ Energy demand components are created through this class by importing csv files.

     :param name: The name given to the energy demand component
     :type name: str
     :param nominal_value: The value that the timeseries should be multipled by, default is 1
     :type nominal_value: numerical

     """

    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)
        # ------------------- PARAMETERS -------------------
        self.name = 'Demand_default_name'

        self.nominal_value = 1
        self.csv_filename = None
        self.csv_separator = ','
        self.column_title = 0
        self.path = os.path.dirname(__file__)

        self.bus_in = None

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)

        # ------------------- READ CSV FILES -------------------
        self.data = func.read_data_file(self.path, self.csv_filename,
                                        self.csv_separator, self.column_title)

    def create_oemof_model(self, busses, _):
        energy_demand_from_csv = solph.Sink(
            label=self.name,
            inputs={busses[self.bus_in]: solph.Flow(
                actual_value=self.data.iloc[self.sim_params.i_interval],
                nominal_value=self.nominal_value,
                fixed=True)})
        return energy_demand_from_csv
