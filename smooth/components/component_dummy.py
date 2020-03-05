import oemof.solph as solph
from .component import Component


class Dummy(Component):
    """Dummy component is created to transform individual specific buses into one general bus"""
    def __init__(self, params):
        # Call the init function of the mother class.
        Component.__init__(self)

        """ PARAMERTERS """
        self.name = 'Dummy_default_name'

        # Busses
        self.bus_in_1 = None
       # self.bus_in_2 = None
        self.bus_out = None

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

    def create_oemof_model(self, busses, _):
        dummy = solph.Transformer(
            label=self.name,
            inputs={busses[self.bus_in_1]: solph.Flow(),
                   #busses[self.bus_in_2]: solph.Flow()
                    },
            outputs={busses[self.bus_out]: solph.Flow()}
          )
        return dummy

