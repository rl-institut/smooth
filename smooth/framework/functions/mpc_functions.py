from oemof import solph
from oemof.outputlib import processing
from scipy.optimize import Bounds, LinearConstraint, minimize
from smooth.framework.functions.debug import get_df_debug, show_debug
from copy import deepcopy
import numpy as np


#--------------------MPC FUNCTIONS--------------------------------------------------------------------------------------

def set_system_input_mpc(components,system_inputs,iteration):
    # call the function with set_system_input_mpc(components,system_inputs,[])
    # if system_inputs is not used with lists
    if iteration==[]:
        for this_in in system_inputs:
            # Loop through all components of the model dict until the right component is found.
            for this_comp in components:
                if this_comp.name == this_in['comp_name']:
                    setattr(this_comp, 'mpc_data', this_in['mpc_data'])
    else:
        for this_in in system_inputs:
            # Loop through all components of the model dict until the right component is found.
            for this_comp in components:
                if this_comp.name == this_in['comp_name']:
                    setattr(this_comp, 'mpc_data', this_in['mpc_data'][iteration])
    return


def create_bounds_mpc(system_inputs, prediction_horizon):
    # Create the bounds as specified in the mpc parameters for all timesteps of the prediction horizon.
    lb = []
    ub = []
    for this_in in system_inputs:
        lb.extend(this_in['lower_bound'] * prediction_horizon)
        ub.extend(this_in['upper_bound'] * prediction_horizon)
    return Bounds(lb, ub)


def create_constraints_mpc(constraints, prediction_horizon):
    # Create the constraints as specified in the mpc parameters for all timesteps of the prediction horizon.
    a = np.empty(0)
    for this_coeff in constraints['coeffs']:
        to_add = np.diagflat([this_coeff] * prediction_horizon)
        if not a.any():
            a = to_add
        else:
            a = np.hstack((a, to_add))
    return LinearConstraint(a, [constraints['lower_bound']] * prediction_horizon,
                            [constraints['upper_bound']] * prediction_horizon)


def model_predictive_control(model, components, system_inputs, prediction_horizon, minimize_options,
                             bounds, constraints, initial_inputs, sim_params_mpc, i_interval):
    def cost_function_mpc(u_vec):
        # Split the optimizer input and save the timeseries in the corresponding system inputs.
        u_vec = u_vec.tolist()
        iter = 0
        for this_in in system_inputs:
            control_data = u_vec[(iter * prediction_horizon):((iter + 1) * prediction_horizon)]
            iter = iter + 1
            this_in['mpc_data'] = control_data
        # Call control model and return overall value of the cost function
        costs = run_model_mpc(model, components, sim_params_mpc, i_interval, prediction_horizon, system_inputs)
        return costs
    # Call the optimizer function with an appropriate method for the system with or without constraints.
    if constraints:
        res = minimize(cost_function_mpc, initial_inputs, method='trust-constr', options=minimize_options,
                       bounds=bounds, constraints=constraints)
    else:
        res = minimize(cost_function_mpc, initial_inputs, method='L-BFGS-B', options = minimize_options,
                       bounds = bounds)
    # Split the optimal input and save the timeseries in the corresponding system inputs.
    iter = 0
    for this_in in system_inputs:
        this_in['mpc_data'] = res.x[(prediction_horizon * iter): (prediction_horizon * (iter + 1))]
        iter = iter + 1
    return system_inputs


def run_model_mpc(model, components_init, sim_params, i_interval_start, prediction_horizon, system_inputs):
    # There are no costs yet.
    costs = 0
    # There are no results yet.
    df_results = None
    results_dict = None
    # Reset sim_params.i_interval to start value.
    sim_params.i_interval = i_interval_start
    # Clone model.
    components = deepcopy(components_init)
    for this_comp in components:
        this_comp.sim_params = sim_params
    # Run the control model for the prediction horizon.
    # ------------------- SIMULATION -------------------
    for i_interval in range(i_interval_start, i_interval_start + prediction_horizon):
        # Save the interval index of this run to the sim_params to make it usable later on.
        sim_params.i_interval = i_interval

        # Set the flows specified as system inputs to the fixed value for this prediction step.
        set_system_input_mpc(components,system_inputs,i_interval-i_interval_start)

        # Initialize the oemof energy system for this time step.
        this_time_index = sim_params.date_time_index[i_interval: (i_interval + 1)]
        oemof_model = solph.EnergySystem(timeindex=this_time_index,
                                         freq='{}min'.format(sim_params.interval_time))

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

        oemof_results = model_to_solve.solve(solver='cbc', solve_kwargs={'tee': False})

        # ------------------- CHECK IF SOLVING WAS SUCCESSFUL -------------------
        # If the status and termination condition is not ok/optimal, get and
        # print the current flows and status
        status = oemof_results["Solver"][0]["Status"].key
        termination_condition = oemof_results["Solver"][0]["Termination condition"].key
        if status != "ok" and termination_condition != "optimal":
            if sim_params.show_debug_flag:
                new_df_results = processing.create_dataframe(model_to_solve)
                df_debug = get_df_debug(df_results, results_dict, new_df_results)
                show_debug(df_debug, components)
                print('solver status: ' + status +
                 " / termination condition: " + termination_condition)
                print(prediction_horizon - i_interval + i_interval_start)
            # If the solution is infeasible, the costs depend on how many prediction steps are left unsolved.
            costs = 1e12 * (prediction_horizon - i_interval + i_interval_start)**2
            return costs
        else:
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
                # Add mpc costs after update of flows and states!
                costs += this_comp.mpc_cost_function()

    if sim_params.show_debug_flag:
        print(costs)
    return costs


def remove_trailing_nones_mpc(this_comp, n_intervals, prediction_horizon):
    # The flows, states and results are initialized for n_interval + prediction_horizon which leads to trailing none
    # values after the simulation has finished. Those trailing none values are removed here.
    for this_flow in this_comp.flows:
        this_comp.flows[this_flow] = this_comp.flows[this_flow][:n_intervals - prediction_horizon]
    for this_state in this_comp.states:
        this_comp.states[this_state] = this_comp.states[this_state][:n_intervals - prediction_horizon]
    this_comp.results['variable_costs'] = this_comp.results['variable_costs'][:n_intervals - prediction_horizon]
    this_comp.results['art_costs'] = this_comp.results['art_costs'][:n_intervals - prediction_horizon]
    this_comp.results['variable_emissions'] = this_comp.results['variable_emissions'][:n_intervals - prediction_horizon]

#---------END MPC FUNCTIONS---------------------------------------------------------------------------------------------