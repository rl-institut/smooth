import os
import oemof.solph as solph
from smooth.components.component import Component
import smooth.framework.functions.functions as func


class EnergyDemandFromCsv(Component):
    """ Energy demand per hour is created through this class from a csv file

    Each line in the csv file represents one timestep and each value
    the respective power demand (e.g. in [W]) at that timestep
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
        # define flow_in
        if self.sim_params.mpc_flag:
            sequence = []
            for i in range(self.sim_params.i_interval,
                           self.sim_params.i_interval + self.sim_params.mpc_control_horizon):
                sequence.extend(self.data.iloc[i].values)
            flow_in = solph.Flow(
                actual_value=sequence,
                nominal_value=self.nominal_value,
                fixed=True)
        else:
            flow_in = solph.Flow(
                actual_value=self.data.iloc[self.sim_params.i_interval],
                nominal_value=self.nominal_value,
                fixed=True)
        # create oemof model
        energy_demand_from_csv = solph.Sink(
            label=self.name,
            inputs={busses[self.bus_in]: flow_in})
        return energy_demand_from_csv
