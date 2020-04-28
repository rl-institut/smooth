from .external_component import ExternalComponent
import os
import smooth.framework.functions.functions as func
from math import ceil


class H2Dispenser(ExternalComponent):
    """ Component created for the dispenser of a refuelling station """

    def __init__(self, params):

        # Call the init function of the mother class.
        ExternalComponent.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = 'Test_additional/external_costs_default_name'

        self.life_time = 20
        # Vehicle tank size: approx. 40 kg for bus and 5 kg for car used as default [kg]
        self.vehicle_tank_size = 40
        # Number of hoses (access points) attached to the dispenser [-]
        self.number_of_hoses = 2
        # The refuelling time to fill up the specified tank [min]
        self.refuelling_time = 15
        self.nominal_value = 1
        self.csv_filename = None
        self.csv_separator = ','
        self.column_title = 0
        self.path = os.path.dirname(__file__)

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)

        # ------------------- READ CSV FILES -------------------
        # The demand csv file is read
        self.data = func.read_data_file(self.path, self.csv_filename, self.csv_separator, self.column_title)

        # ------------------- CALCULATED PARAMETERS -------------------
        # The maximum value per timestep is found
        self.max_hourly_h2_demand = self.data.values.max()
        # Calculates how many times each hose can refuel a vehicle per hour
        self.number_of_refuels_per_hour = 60/self.refuelling_time
        # Calculates the maximum amount of vehicles that need refuelling per hour
        self.max_number_of_vehicles = self.max_hourly_h2_demand/self.vehicle_tank_size
        # Calculates number of dispenser units required in order to satisfy the demand
        self.number_of_units =\
            ceil(self.max_number_of_vehicles/(self.number_of_hoses * self.number_of_refuels_per_hour))
