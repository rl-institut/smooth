import os
import oemof.solph as solph
from smooth.components.component import Component
import smooth.framework.functions.functions as func


class EnergySourceFromCsv (Component):
    """General energy source components are created through this class by importing csv files.

    :param name: The name given to the energy source component
    :type name: str
    :param nominal_value: The value that the timeseries should be multiplied by, default is 1
    :type nominal_value: numerical
    :param csv_filename: The csv filename containing the desired timeseries, e.g. 'my_filename.csv'
    :type csv_filename: str
    :param csv_separator: The separator of the csv file, e.g. ';' or ',' (default is ';')
    :type csv_separator: str
    :param column_title: The column title (or index) of the timeseries, default is 0
    :type column_title: str or int
    :param path: The path where the timeseries csv file can be located
    :type path: str
    :param bus_out: The virtual bus that leaves the energy source component (e.g. the electricity bus, 'bel')
    :type bus_out: str
    :param set_parameters(params): Updates parameter default values
    :type set_parameters(params): function (see generic Component class)
    :param data: Dataframe containing data from timeseries
    :type data: pandas dataframe
    """

    def __init__(self, params):
        """Constructor method
        """
        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = 'General_energy_source'
        self.nominal_value = 1
        self.reference_value = 1
        self.csv_filename = None
        self.csv_separator = ','
        self.column_title = 0
        self.path = os.path.dirname(__file__)
        self.bus_out = None

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)

        # ------------------- READ CSV FILES -------------------
        self.data = func.read_data_file(self.path, self.csv_filename,
                                        self.csv_separator, self.column_title)

    def create_oemof_model(self, busses, _):
        """Creates an oemof Source component from the information given in the
        EnergySourceFromCSV class, to be used in the oemof model.

        :param busses: List of the virtual buses used in the energy system
        :type busses: list
        :param _: ToDo: check how to define this
        :return: The 'energy_source_from_csv' oemof component
        """
        energy_source_from_csv = solph.Source(
            label=self.name,
            outputs={busses[self.bus_out]: solph.Flow(
                actual_value=self.data.iloc[self.sim_params.i_interval],
                nominal_value=self.nominal_value,
                fixed=True)})
        return energy_source_from_csv
