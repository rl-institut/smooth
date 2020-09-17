from oemof import solph
from oemof.outputlib import processing
from smooth.framework.simulation_parameters import SimulationParameters as sp
from smooth.framework.functions.debug import get_df_debug, show_debug
from smooth.framework.exceptions import SolverNonOptimalError
from smooth.framework.functions.functions import create_component_obj
import smooth.framework.functions.mpc_functions as mpc
from copy import deepcopy


def run_smooth(model):
    # Run the smooth simulation framework.
    # Parameters:
    #  model: smooth model object containing parameters for components, simulation and busses.

    # ------------------- INITIALIZATION -------------------
    # legacy: components may be list. Convert to dict.
    if isinstance(model["components"], list):
        names = [c.pop("name") for c in model["components"]]
        model.update({'components': dict(zip(names, model["components"]))})

    # USE MPC ALGORITHM?
    mpc_params = model.get('mpc_params', {})
    if 'prediction_horizon' in mpc_params:
        prediction_horizon = mpc_params['prediction_horizon']
        # create initial inputs for the mpc optimization
        initial_inputs = []
        for this_in in mpc_params['system_inputs']:
            initial_inputs.extend([this_in['mpc_data']] * mpc_params['prediction_horizon'])
        # create bounds and constraints for the mpc optimization
        bounds = mpc.create_bounds_mpc(mpc_params['system_inputs'], mpc_params['prediction_horizon'])
        if mpc_params['constraints']:
            constraints = mpc.create_constraints_mpc(mpc_params['constraints'], mpc_params['prediction_horizon'])
        else:
            constraints = []
        # GET SIMULATION PARAMETERS
        # Create a simulation parameters object with extended date time index
        model['sim_params']['n_intervals'] = model['sim_params']['n_intervals'] + mpc_params['prediction_horizon']
        sim_params = sp(model['sim_params'])
        # deep copy simulation parameters for mpc
        sim_params_mpc = deepcopy(sim_params)
    else:
        prediction_horizon = 0
        # GET SIMULATION PARAMETERS
        sim_params = sp(model['sim_params'])
        # ensure that all operate_on_mpc attributes are False.
        for this_comp in model['components']:
            if 'operate_on_mpc' in model['components'][this_comp]:
                model['components'][this_comp]['operate_on_mpc'] = False


    # CREATE COMPONENT OBJECTS
    components = create_component_obj(model, sim_params)

    # There are no results yet.
    df_results = None
    results_dict = None

    # ------------------- SIMULATION -------------------
    for i_interval in range(sim_params.n_intervals - prediction_horizon):
        # Save the interval index of this run to the sim_params to make it usable later on.
        sim_params.i_interval = i_interval
        if sim_params.print_progress:
            print('Simulating interval {}/{}'.format(i_interval+1, sim_params.n_intervals - prediction_horizon))

        # Initialize the oemof energy system for this time step.
        this_time_index = sim_params.date_time_index[i_interval: (i_interval + 1)]
        oemof_model = solph.EnergySystem(timeindex=this_time_index,
                                         freq='{}min'.format(sim_params.interval_time))

        if 'prediction_horizon' in mpc_params:
            mpc_params['system_inputs'] = mpc.model_predictive_control(model, components, mpc_params['system_inputs'],
                                                                        mpc_params['prediction_horizon'],
                                                                        mpc_params['minimize_options'],
                                                                        bounds, constraints,
                                                                        initial_inputs, sim_params_mpc, i_interval)
            mpc.set_system_input_mpc(components, mpc_params['system_inputs'], iteration=0)
            initial_inputs = []
            for this_in in mpc_params['system_inputs']:
                initial_inputs.extend(this_in['mpc_data'][1:])
                initial_inputs.append(initial_inputs[-1])

        # ------------------- CREATE THE OEMOF MODEL FOR THIS INTERVAL -------------------
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
            # Get the oemof representation of this component.
            this_oemof_model = this_comp.create_oemof_model(busses, oemof_model)
            if this_oemof_model is not None:
                # Add the component to the oemof model.
                oemof_model.add(this_oemof_model)
            else:
                # If None is given back, no model is supposed to be added.
                pass

        # ------------------- RUN THE SIMULATION -------------------
        # Do the simulation for this time step.
        model_to_solve = solph.Model(oemof_model)

        for this_comp in components:
            this_comp.update_constraints(busses, model_to_solve)

        if i_interval == 0:
            # Save the set of linear equations for the first interval.
            model_to_solve.write('./oemof_model.lp', io_options={'symbolic_solver_labels': True})

        oemof_results = model_to_solve.solve(solver='cbc', solve_kwargs={'tee': False})

        # ------------------- CHECK IF SOLVING WAS SUCCESSFUL -------------------
        # If the status and temination condition is not ok/optimal, get and
        # print the current flows and status
        status = oemof_results["Solver"][0]["Status"].key
        termination_condition = oemof_results["Solver"][0]["Termination condition"].key
        if status != "ok" and termination_condition != "optimal":
            if sim_params.show_debug_flag:
                new_df_results = processing.create_dataframe(model_to_solve)
                df_debug = get_df_debug(df_results, results_dict, new_df_results)
                show_debug(df_debug, components)
            raise SolverNonOptimalError('solver status: ' + status +
                                        " / termination condition: " + termination_condition)

        # ------------------- HANDLE RESULTS -------------------
        # Get the results of this oemof run.
        results = processing.results(model_to_solve)
        results_dict = processing.parameter_as_dict(model_to_solve)
        df_results = processing.create_dataframe(model_to_solve)

        # Loop through every component and call the result handling functions
        for this_comp in components:
            # Update the flows
            this_comp.update_flows(results, sim_params)
            # Update the states.
            this_comp.update_states(results, sim_params)
            # Update the costs and artificial costs.
            this_comp.update_var_costs(results, sim_params)
            # Update the costs and artificial costs.
            this_comp.update_var_emissions(results, sim_params)

    # Calculate the annuity for each component.
    for this_comp in components:
        this_comp.generate_results()
        if 'prediction_horizon' in mpc_params:
            # remove trailing none values:
            mpc.remove_trailing_nones_mpc(this_comp, sim_params.n_intervals, mpc_params['prediction_horizon'])
    if 'prediction_horizon' in mpc_params:
        # cut off the additional entries in sim_params.date_time_index
        sim_params.date_time_index = sim_params.date_time_index[:sim_params.n_intervals - mpc_params['prediction_horizon']]
        sim_params.n_intervals = sim_params.n_intervals - mpc_params['prediction_horizon']

    return components, status
