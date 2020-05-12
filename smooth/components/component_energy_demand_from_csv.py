import os
import oemof.solph as solph
from smooth.components.component import Component
import smooth.framework.functions.functions as func


class EnergyDemandFromCsv(Component):
    """Energy demand components are created through this class by importing csv files.

     :param name: The name given to the energy demand component
     :type name: str
     :param nominal_value: The value that the timeseries should be multipled by, default is 1
     :type nominal_value: numerical
     :param csv_filename: The csv filename containing the desired demand timeseries e.g. 'my_demand_filename.csv'
     :type csv_filenmae: str
     :param csv_separator: The separator of the csv file e.g. ',' or ';', default is ','
     :type csv_separator: str
     :param column_title: The column title (or index) of the timeseries, default is 0
     :type column_title: str or int
     :param path: The path where the timeseries csv file can be located
     :type path: str
     :param bus_in: The virtual bus that enters the energy demand component (e.g. the hydrogen bus)
     :type bus_in: str
     :param set_parameters(params): Updates parameter default values (see generic Component class)
     :type set_parameters(params): function
     :param data: Dataframe containing data from timeseries
     :type data: pandas dataframe
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
        """Creates an oemof Sink component from the information given in the EnergyDemandFromCSV class, to be used in the oemof model.

        :param busses: List of the virtual buses used in the energy system
        :type busses: list
        :param _: ToDo: check this
        :return: The 'energy_demand_from_csv' oemof component
        """
        energy_demand_from_csv = solph.Sink(
            label=self.name,
            inputs={busses[self.bus_in]: solph.Flow(
                actual_value=self.data.iloc[self.sim_params.i_interval],
                nominal_value=self.nominal_value,
                fixed=True)})
        return energy_demand_from_csv
