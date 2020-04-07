import os
import oemof.solph as solph
from smooth.components.component import Component
import smooth.framework.functions.functions as func


class H2RefuelCoolingSystem(Component):
    """ A component that represents the cooling system in a refuelling station

     TO BE USED IN MODEL DEFINITION/JSON FILE:
     -	CAPEX: 140,000 €
     -	OPEX 5 % der CAPEX"""

    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)
        """ PARAMETERS """
        self.name = 'H2_refuel_default_name'

        self.bus_el = None

        self.nominal_value = 1
        self.csv_filename = None
        self.csv_separator = ','
        self.column_title = 0
        self.path = os.path.dirname(__file__)

        # the energy required to cool the refuelling station [kJ/kg]
        self.cool_spec_energy = 730
        # the required standby energy [kJ/h]
        self.standby_energy = 8100
        # lifetime of the component [years]
        self.life_time = 20
        # number of units [-]
        self.number_of_units = 1

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

        """ READ CSV FILES """
        self.data = func.read_data_file(self.path, self.csv_filename, self.csv_separator, self.column_title)

        # calculate the electrical energy required for each hour [Wh]
        self.electrical_energy = \
            (self.data*self.cool_spec_energy + self.standby_energy) / 3.6

        """ STATES """
    def create_oemof_model(self, busses, _):
        h2_refuel_cooling_system = solph.Sink(
            label=self.name,
            inputs={busses[self.bus_el]: solph.Flow(
                    actual_value=self.electrical_energy.iloc[self.sim_params.i_interval],
                    nominal_value=self.nominal_value,
                    fixed=True
                )})
        return h2_refuel_cooling_system
