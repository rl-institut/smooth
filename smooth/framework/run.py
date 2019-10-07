import importlib
from oemof import solph
from oemof.outputlib import processing
from smooth.framework.simulation_parameters import SimulationParameters as sp


def run(model):
    # Run the smooth simulation framework.
    # Parameters:
    #  model: smooth model object containing parameters for components, simulation and busses.

    """ INITIALIZATION """
    # CHECK IF COMPONENT NAMES ARE UNIQUE
    # Check if all component names are unique, otherwise throw an error. Therefor first get all component names.
    comp_names = []
    for this_comp in model['components']:
        comp_names.append(this_comp['name'])

    # Then check if all component names are unique.
    for this_comp_name in comp_names:
        if comp_names.count(this_comp_name) is not 1:
            raise ValueError('Component name "{}" is not unique, please name components unique.'.format(this_comp_name))

    # GET SIMULATION PARAMETERS
    # Create an object with the simulation parameters.
    sim_params = sp(model['sim_params'])

    # CREATE COMPONENT OBJECTS
    components = []
    for this_comp in model['components']:
        # Add the simulation step size to the component info [min].
        this_comp['interval_time'] = sim_params.interval_time
        # Loop through all components of the model and load the component classes.
        this_comp_name = this_comp['component']
        # Import the module of the component.
        this_comp_module = importlib.import_module('smooth.components.component_' + this_comp_name)
        # While class name is camel case, underscores has to be removed and letters after underscores have to be capital
        class_name = ''
        if this_comp_name.isupper():
            class_name = this_comp_name
        else:
            this_comp_name_split = this_comp_name.split('_')
            for this_comp_name_part in this_comp_name_split:
                class_name += this_comp_name_part.capitalize()
        # Load the class (which by convention has a name with a capital first letter and camel case).
        this_comp_class = getattr(this_comp_module, class_name)
        # Initialize the component.
        components.append(this_comp_class(this_comp))

    """ SIMULATION """
    for i_interval in range(sim_params.n_intervals):
        # Save the interval index of this run to the sim_params to make it usable later on.
        sim_params.i_interval = i_interval
        print('Simulating interval {}/{}'.format(i_interval, sim_params.n_intervals))
        # Initialize the oemof energy system for this time step.
        this_time_index = sim_params.date_time_index[i_interval: (i_interval + 1)]
        oemof_model = solph.EnergySystem(timeindex=this_time_index, freq='H')

        """ CREATE THE OEMOF MODEL FOR THIS INTERVAL """
        # Create all busses and save them to a dict for later use in the components.
        busses = {}

        for i_bus in model['busses']:
            # Create this bus and append it to the "busses" dict.
            busses[i_bus] = solph.Bus(label=i_bus)
            # Add the bus to the simulation model.
            oemof_model.add(busses[i_bus])

        # Prepare the simulation.
        for this_comp in components:
            # Execute the prepare simulation step (if this component has one).
            this_comp.prepare_simulation(components)
            # Add the component to the oemof model.
            oemof_model.add(this_comp.create_oemof_model(busses, sim_params))

        """ RUN THE SIMULATION """
        # Do the simulation for this time step.
        model_to_solve = solph.Model(oemof_model)
        model_to_solve.solve(solver='cbc', solve_kwargs={'tee': False})

        """ CHECK IF SOLVING WAS SUCCESSFUL """
        # Get the meta results.
        meta_results = processing.meta_results(model_to_solve)

        """ HANDLE RESULTS """
        # Get the results of this oemof run.
        results = processing.results(model_to_solve)

        # Loop through every component and call the result handling functions
        for this_comp in components:
            # Update the flows
            this_comp.update_flows(results, sim_params)
            # Update the states.
            this_comp.update_states(results, sim_params)
            # Update the costs and artificial costs.
            this_comp.update_costs(results, sim_params)

    """ VIEWING RESULTS """
    # can be deleted but displays results for flows/states of components
    for this_comp in components:
        print('Comp: {}: flow: {}'.format(this_comp.name, this_comp.flows))

    print('Simulation done')







