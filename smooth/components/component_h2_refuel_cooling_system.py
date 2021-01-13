"""
A component that represents the cooling system in a refuelling station is
created through this class.

*****
Scope
*****
As part of the hydrogen refuelling station, a cooling system is required
to precool high pressure hydrogen before it is dispensed into the vehicle's
tank. This is in order to prevent the tank from overheating.

*******
Concept
*******
An oemof Sink component is used which has one electrical bus input that
represents the electricity required to power the cooling system.

.. figure:: /images/h2_refuel_cooling_system.png
    :width: 40 %
    :alt: h2_refuel_cooling_system.png
    :align: center

    Fig.1: Simple diagram of a hydrogen refuel cooling system.

The required electricity supply for the cooling system per timestep is
calculated by the following equation:

.. math::
    E_{elec,i} = \\frac{D_{H_{2},i} \\cdot E_{spec} + E_{standby}}{3.6}

* :math:`E_{elec,i}` = electrical energy required for the ith timestep [Wh]
* :math:`D_{H_{2},i}` = hydrogen demand for the ith timestep [kg]
* :math:`E_{spec}` = specific energy required relative to the demand [kJ/kg]
* :math:`E_{standby}` = standby energy required per timestep [kJ/h]

The default specific energy is chosen to be 730 kJ/kg, and the standby
energy is chosen to be 8100 kJ/h [find source]. Furthermore, this
cooling system component is only necessary if the hydrogen is compressed
over 350 bar e.g. to 700 bar for passenger cars.
"""


import os
import oemof.solph as solph
from smooth.components.component import Component
import smooth.framework.functions.functions as func


class H2RefuelCoolingSystem(Component):
    """
    :param name: unique name given to the H2 refuel cooling system component
    :type name: str
    :param bus_el: electricity bus that is the input of the cooling system
    :type bus_el: str
    :param nominal_value: value that the timeseries should be multiplied by, default is 1
    :type nominal_value: numerical
    :param csv_filename: csv filename containing the desired timeseries, e.g. 'my_filename.csv'
    :type csv_filename: str
    :param csv_separator: separator of the csv file, e.g. ',' or ';' (default is ',')
    :type csv_separator: str
    :param column_title: column title (or index) of the timeseries, default is 0
    :type column_title: str or int
    :param path: path where the timeseries csv file can be located
    :type path: str
    :param cool_spec_energy: energy required to cool the refuelling station [kJ/kg]
    :type cool_spec_energy: numerical
    :param standby_energy: required standby energy [kJ/h]
    :type standby_energy: numerical
    :param life_time: life time of the component [a]
    :type life_time: numerical
    :param number_of_units: number of units installed
    :type number of units: numerical
    :param set_parameters(params): updates parameter default values
        (see generic Component class)
    :type set_parameters(params): function
    :param data: dataframe containing data from timeseries
    :type data: pandas dataframe
    :param electrical_energy: electrical energy required for each hour [Wh]
    :type electrical_energy: numerical
    """

    def __init__(self, params):
        """Constructor method
        """
        # Call the init function of the mother class.
        Component.__init__(self)
        # ------------------- PARAMETERS -------------------
        self.name = 'H2_refuel_default_name'
        self.bus_el = None
        self.nominal_value = 1
        self.csv_filename = None
        self.csv_separator = ','
        self.column_title = 0
        self.path = os.path.dirname(__file__)
        self.cool_spec_energy = 730
        self.standby_energy = 8100
        self.life_time = 20
        self.number_of_units = 1

        # ------------------- UPDATE PARAMETER DEFAULT VALUES -------------------
        self.set_parameters(params)

        # ------------------- READ CSV FILES -------------------
        self.data = func.read_data_file(self.path, self.csv_filename,
                                        self.csv_separator, self.column_title)

        self.electrical_energy = \
            (self.data * self.cool_spec_energy + self.standby_energy) / 3.6

    def create_oemof_model(self, busses, _):
        """Creates an oemof Sink component from information given in
        the H2RefuelCoolingSystem class, to be used in the oemof model

        :param busses: virtual buses used in the energy system
        :type busses: list
        :return: oemof 'h2_refuel_cooling_system' component
        """
        h2_refuel_cooling_system = solph.Sink(
            label=self.name,
            inputs={busses[self.bus_el]: solph.Flow(
                    actual_value=self.electrical_energy.iloc[self.sim_params.i_interval],
                    nominal_value=self.nominal_value,
                    fixed=True
                    )})
        return h2_refuel_cooling_system
