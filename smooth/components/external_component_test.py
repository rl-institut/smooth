from .external_component import ExternalComponent
import oemof.solph as solph


class Test(ExternalComponent):
    """ Component created as a test for additional/external costs outside of optimization """

    def __init__(self, params):

        # Call the init function of the mother class.
        ExternalComponent.__init__(self)
        """ PARAMETERS """
        self.name = 'Test_additional/external_costs_default_name'
        self.number_of_units = 5
        self.life_time = 20

        self.bus_in = None

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)



