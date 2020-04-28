from .external_component import ExternalComponent
import oemof.solph as solph


class Dispenser(ExternalComponent):
    """ Component created for the dispenser of a refuelling station """

    def __init__(self, params):

        # Call the init function of the mother class.
        ExternalComponent.__init__(self)
        
        """ PARAMETERS """
        self.name = 'Test_additional/external_costs_default_name'
        self.number_of_units = 5
        self.life_time = 20

        self.nominal_value = 1
        self.csv_filename = None
        self.csv_separator = ','
        self.column_title = 0
        self.path = os.path.dirname(__file__)

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)



