import oemof.solph as solph
from .component import Component
from oemof.outputlib import views

class Storage (Component):
    """ Storage agents are created through this class """
    def __init__(self, params):

        # Call the init function of the mother class.
        Component.__init__(self)

        """ PARAMETERS """
        self.name = 'Storage_default_name'
        self.component = 'Storage'
        self.storage_capacity = 500
        self.storage_level_init = 200
        self.storage_level_min = 100
        self.capex_per_unit = 1000
        self.opex_per_unit = 100

        self.bus_in_and_out = None

        """ PARAMETERS (VARIABLE ARTIFICIAL COSTS - VAC) """
        # Normal var. art. costs for charging (in) and decharging (out) the storage [EUR/kg].
        self.vac_in = 0
        self.vac_out = 0
        # If a storage level is set as wanted, the vac_low costs apply if the storage is below that level [kg].
        self.storage_level_wanted = None
        # Var. art. costs that apply if the storage level is below the wanted storage level [EUR/kg].
        self.vac_low_in = 0
        self.vac_low_out = 0

        """ UPDATE PARAMETER DEFAULT VALUES """
        self.set_parameters(params)

        """ STATES """
        # Storage level [kg of h2]
        self.storage_level = self.storage_level_init

        """ VARIABLE ARTIFICIAL COSTS """
        # Store the current artificial costs for input and output [EUR/kg].
        self.current_vac = [0, 0]

    def prepare_simulation(self, components):
        # Set the var. art. costs.
        vac_in = self.vac_in
        vac_out = self.vac_out

        if self.storage_level_wanted is not None and self.storage_level < self.storage_level_wanted:
            # If a wanted storage level is set and the storage level fell below that wanted level, the low VAC apply.
            vac_in = self.vac_low_in
            vac_out = self.vac_low_out

        self.current_vac = [vac_in, vac_out]

    def create_oemof_model(self, busses, sim_params):
        storage = solph.components.GenericStorage(
            label=self.name,
            outputs={busses[self.bus_in_and_out]: solph.Flow(variable_costs=self.current_vac[1])},
            inputs={busses[self.bus_in_and_out]: solph.Flow(variable_costs=self.current_vac[0])},
            initial_storage_level=self.storage_level / self.storage_capacity,
            nominal_storage_capacity=self.storage_capacity,
            min_storage_level=self.storage_level_min / self.storage_capacity,
            balanced=False)
        return storage

    def update_states(self, results, sim_params):
        data_storage = views.node(results, self.name)
        df_storage = data_storage['sequences']

        # Loop Through the data frame values and update states accordingly.
        for i_result in df_storage:
            if i_result[1] == 'capacity':
                if 'storage_level' not in self.states:
                    # Initialize an array that tracks the state stored mass.
                    self.states['storage_level'] = [None] * sim_params.n_intervals
                # Check if this result is the storage capacity.
                self.states['storage_level'][sim_params.i_interval] = df_storage[i_result][0]
                self.storage_level = df_storage[i_result][0]







