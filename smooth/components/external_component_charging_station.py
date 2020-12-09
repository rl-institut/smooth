from .external_component import ExternalComponent
import os
import smooth.framework.functions.functions as func
from math import ceil


class ChargingStation(ExternalComponent):
    """ Component created for the dispenser of a refuelling station """

    def __init__(self, params):

        # Call the init function of the mother class.
        ExternalComponent.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = 'charging_station_default_name'

        self.life_time = 20
        # Output_max: Power output [W]
        self.output_max = 20000
        # Number of parallel ports (access points) attached to one charging station [-]
        self.number_of_parallel_ports = 1
        # conversion factor to SI based units, normally [W]
        self.conversion_factor = 1
        self.csv_filename = None
        self.csv_separator = ','
        self.column_title = 0
        self.path = os.path.dirname(__file__)

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)

        # ------------------- READ CSV FILES -------------------
        # The demand csv file is read
        self.data = func.read_data_file(self.path, self.csv_filename,
                                        self.csv_separator, self.column_title)
        # Convert input data to SI based units
        self.data = self.data * self.conversion_factor
        # ------------------- CALCULATED PARAMETERS -------------------
        # Maximum power demand
        self.max_demand = self.data.values.max()
        # Calculates the maximum amount of vehicles charged in parallel at all charging stations
        self.max_number_of_vehicles = self.max_demand/self.output_max
        # Calculates number of dispenser units required in order to satisfy the demand
        self.number_of_units =\
            ceil(self.max_number_of_vehicles/self.number_of_parallel_ports)
