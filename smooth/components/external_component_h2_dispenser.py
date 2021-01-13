"""
This external component class is created to represent the dispenser unit
of a hydrogen refuelling station.

*****
Scope
*****
The dispenser unit of a hydrogen refuelling station does not need to be
included in the optimization of an energy system, as the number of units
necessary can be calculated from the hydrogen demand, but the costs of
the dispensers should be considered in the final evaluation of the energy
system.

*******
Concept
*******
This component requires a demand time series in the form of a CSV file. From
this file, the maximum hydrogen demand in one time step is found. Then, the
number of times each hose can refuel a vehicle per hour is calculated, as
well as the maximum number of vehicles that require refuelling per hour.
The number of dispenser units required is then calculated as follows:

.. math::
    U = \\frac{V_{max}}{H \\cdot R}

* :math:`U` = number of dispenser units required [-]
* :math:`V_{max}` = maximum number of vehicles that need refuelling in an hour [-]
* :math:`H` = number of hoses per dispenser [-]
* :math:`R` = number of possible refuels per hour [-]
"""


from .external_component import ExternalComponent
import os
import smooth.framework.functions.functions as func
from math import ceil


class H2Dispenser(ExternalComponent):
    """
    :param name: unique name given to the H2 dispenser component
    :type name: str
    :param life_time: life time of the component [a]
    :type life_time: numerical
    :param vehicle_tank_size: vehicle tank size - 40 kg for a bus and 5 kg for a
        passenger car are used as default [kg]
    :type vehicle_tank_size: numerical
    :param number_of_hoses: number of hoses (access points) attached to the
        dispenser - default is set to 2 [-]
    :type number_of_hoses: int
    :param refuelling_time: refuelling time to fill up the specified tank [min]
        - default is set to 15
    :type refuelling_time: numerical
    :param nominal_value: value that the timeseries should be multipled by, default is 1
    :type nominal_value: numerical
    :param csv_filename: csv filename containing the desired demand timeseries e.g.
        'my_demand_filename.csv'
    :type csv_filenmae: str
    :param csv_separator: separator of the csv file e.g. ',' or ';', default is ','
    :type csv_separator: str
    :param column_title: column title (or index) of the timeseries, default is 0
    :type column_title: str or int
    :param path: path where the timeseries csv file can be located
    :type path: str
    :param set_parameters(params): updates parameter default values
        (see generic Component class)
    :type set_parameters(params): function
    :param data: dataframe containing data from timeseries
    :type data: pandas dataframe
    :param max_hourly_h2_demand: maximum value per timestep
    :type max_hourly_h2_demand: numerical
    :param number_of_refuels_per_hour: number of times each hose can refuel a
        vehicle per hour
    :type number_of_refuels_per_hour: numerical
    :param max_number_of_vehicles: maximum amount of vehicles that need
        refuelling per hour
    :type max_number_of_vehicles: numerical
    :param number_of_units: number of dispenser units required in order to
        satisfy the demand
    :type number_of_units: numerical
    """

    def __init__(self, params):
        """Constructor method
        """
        # ToDo: change from hour to flexible timestep!
        # Call the init function of the mother class.
        ExternalComponent.__init__(self)

        # ------------------- PARAMETERS -------------------
        self.name = 'Test_additional/external_costs_default_name'

        self.life_time = 20
        self.vehicle_tank_size = 40
        self.number_of_hoses = 2
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
        self.data = func.read_data_file(self.path, self.csv_filename,
                                        self.csv_separator, self.column_title)

        # ------------------- CALCULATED PARAMETERS -------------------
        self.max_hourly_h2_demand = self.data.values.max()
        self.number_of_refuels_per_hour = 60/self.refuelling_time
        self.max_number_of_vehicles = self.max_hourly_h2_demand/self.vehicle_tank_size
        self.number_of_units =\
            ceil(self.max_number_of_vehicles/(self.number_of_hoses *
                                              self.number_of_refuels_per_hour))
