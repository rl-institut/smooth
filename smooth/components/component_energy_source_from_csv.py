import os
import oemof.solph as solph
from smooth.components.component import Component
import smooth.framework.functions.functions as func


class EnergySourceFromCsv (Component):
    """ General energy sources are created through this class by importing csv files

    Each line in the csv file represents one timestep and each value
    the respective power (e.g. in [W]) coming from the energy source at that timestep
    """

    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = 'General_energy_source'

        self.nominal_value = 1
        self.reference_value = 1
        self.csv_filename = None
        self.csv_separator = ';'
        self.column_title = 0
        self.path = os.path.dirname(__file__)
        self.bus_out = None

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)

        # ------------------- READ CSV FILES -------------------
        self.data = func.read_data_file(self.path, self.csv_filename,
                                        self.csv_separator, self.column_title)

    def create_oemof_model(self, busses, _):
        # define flow_out
        if self.sim_params.mpc_flag:
            sequence = []
            for i in range(self.sim_params.i_interval,
                           self.sim_params.i_interval + self.sim_params.mpc_control_horizon):
                sequence.extend(self.data.iloc[i].values)
            flow_out = solph.Flow(
                # actual_value=self.data.iloc[self.sim_params.i_interval:
                #                             (self.sim_params.i_interval +
                #                              self.sim_params.mpc_control_horizon)].values.tolist(),
                actual_value = sequence,
                nominal_value=self.nominal_value,
                fixed=True)
        else:
            flow_out = solph.Flow(
                actual_value=self.data.iloc[self.sim_params.i_interval],
                nominal_value=self.nominal_value,
                fixed=True)
        # create oemof model
        energy_source_from_csv = solph.Source(
            label=self.name,
            outputs={busses[self.bus_out]: flow_out})
        return energy_source_from_csv
