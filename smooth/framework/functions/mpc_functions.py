from oemof.outputlib import views
from oemof import solph
from oemof.outputlib import processing
import math
from scipy.optimize import Bounds, LinearConstraint, minimize
import numpy as np
from smooth.framework.functions.debug import get_df_debug, show_debug
from copy import deepcopy
from smooth.framework.functions.load_results import load_results


#--------------------MPC FUNCTIONS--------------------------------------------------------------------------------------
def run_mpc_dummy(this_model,components,system_outputs,iteration,sim_params):
    # function calculating the system inputs (control variables) based on the system outputs
    # (controlled process variables) and a (dummy) mpc algorithm
    # system inputs
    time_end = sim_params.n_intervals
    system_inputs = define_system_inputs_mpc() # auslagern und Aufruf in run_smooth???!!!
    # system_inputs['power_electrolyzer']['mpc_data'] = [0.6]*time_end
    # system_inputs['mflow_h2_storage']['mpc_data'] = sine_list_input_mpc(0,0.01,time_end) # 0.50
    sequence_ely = pickle_input_mpc('this_ely',1)
    sequence_ely = [x/190000 for x in sequence_ely]
    sequence_storage = pickle_input_mpc('h2_storage_lp',1)
    sequence_storage = [x/(60/9) for x in sequence_storage]
    system_inputs['power_electrolyzer']['mpc_data'] = sequence_ely
    system_inputs['mflow_h2_storage']['mpc_data'] = sequence_storage
    set_system_input_mpc(components,system_inputs,iteration)
    return

def set_system_input_mpc(components,system_inputs,iteration):
    # rufe die function mit set_system_input_mpc(components,system_inputs,[]) auf,
    # wenn system_inputs nicht mit Vektoren verwendet wird
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


def get_system_output_mpc(results,system_outputs):
    # rufe die function mit get_system_output_mpc(results,[]) auf, um system_outputs nur für den aktuelle Zeitschritt
    # zu speichern
    # sonst werden die aktuellen Werte an die Liste der vorherigen Werte angehängt
    if not system_outputs:
        system_outputs = define_system_outputs_mpc()
        # loop through all system outputs and get the current flow values
        for this_out in system_outputs:
            this_comp_node = views.node(results, this_out['node1_name'])
            try:
                this_df = this_comp_node['sequences']
                for i_result in this_df:
                    # check if i_result is the desired flow
                    # oemof-Doku zu outputlib: flow-keys: (node1,node2); node-keys: (node,None)
                    if i_result[0][0] == this_out['node1_name'] and i_result[0][1] == this_out['node2_name']:
                        # flow from node1 to node2
                        this_out['flow_value'] = [this_df[i_result][0]]
                        # print(this_out['flow_value'])
                break
            except KeyError:
                print('KeyError( sequences) in ', this_out)
                # this_out['flow_value'] = [math.nan]
    else:
        # loop through all system outputs and get the current flow values
        for this_out in system_outputs:
            this_comp_node = views.node(results, this_out['node1_name'])
            this_df = this_comp_node['sequences']
            for i_result in this_df:
                # check if i_result is the desired flow
                # oemof-Doku zu outputlib: flow-keys: (node1,node2); node-keys: (node,None)
                if i_result[0][0] == this_out['node1_name'] and i_result[0][1] == this_out['node2_name']:
                    # flow from node1 to node2
                    this_out['flow_value'] = this_out['flow_value'] + [this_df[i_result][0]]
    return system_outputs


def define_system_inputs_mpc():
    # define the system inputs of your MIMO System
    electrolyzer = {
        'comp_name': 'this_ely',
        'mpc_data': 0,
        'lower_bound': [0],
        'upper_bound': [1],
    }
    h2_storage = {
        'comp_name': 'h2_storage_lp',
        'mpc_data': 0,
        'lower_bound': [0],
        'upper_bound': [1],
    }
    system_inputs = {'power_electrolyzer': electrolyzer, 'mflow_h2_storage': h2_storage}
    # system_inputs = {'power_electrolyzer': electrolyzer}
    return system_inputs


def define_system_outputs_mpc():
    # define the system outputs of your MIMO System
    supply_el = {
        'node1_name': 'from_grid',
        'node2_name': 'bel',
        'flow_value': [0],
    }
    sink_el = {
        'node1_name': 'bel',
        'node2_name': 'to_grid',
        'flow_value': [0],
    }
    to_demand_h2_mp = {
        'node1_name': 'bh2_mp',
        'node2_name': 'h2_demand_mp',
        'flow_value': [0],
    }
    compressor_h2_mp = {
        'node1_name': 'h2_compressor_mp',
        'node2_name': 'bh2_mp',
        'flow_value': [0],
    }
    supply_h2_mp = {
        'node1_name': 'h2_grid',
        'node2_name': 'bh2_mp',
        'flow_value': [0],
    }
    sink_h2_mp = {
        'node1_name': 'bh2_mp',
        'node2_name': 'h2_sink',
        'flow_value': [0],
    }
    system_outputs = [supply_el, sink_el, to_demand_h2_mp, compressor_h2_mp, supply_h2_mp, sink_h2_mp]
    # system_outputs = [supply_el, sink_el, to_demand_h2_mp, compressor_h2_mp]
    # To Do: initialize flow values with NaN and set starting values only when requested when the method is called
    return system_outputs


def pickle_input_mpc(comp_name, flow_switch):
    # comp_name is the name of the component containing the desired flow
    # flow_switch can only be 0 or 1, 0: outflow, 1: inflow
    results = load_results(
        'C:/Users/ulrike.herrmann/PycharmProjects/271_Ulrike/MPC/2020-06-26_11-30-38_linearized_model_day1.pickle')
    data = views.node(results, comp_name)
    df = data['sequences']
    for i_result in df:
        if i_result[0][flow_switch] == comp_name and i_result[1] == 'flow':
            flow_sequence = df[i_result].values.tolist()
    return flow_sequence


def step_input_mpc(operating_point,step_size,iteration,time_end):
    # function returning the current value of a step signal
    # start in operation point, step up and down with specified step size
    step = [operating_point]*5+[operating_point+step_size]*5+[operating_point-step_size]*5+[operating_point]*(time_end-15) # *(9+6*24)
    return step[iteration]


def sine_input_mpc(operating_point,amplitude,iteration,time_end):
    time = range(1,time_end+1)
    time_sine = [math.sin(t) for t in time]
    sine = [operating_point + amplitude*y for y in time_sine]
    return sine[iteration]


def sine_list_input_mpc(operating_point,amplitude,time_end):
    time = range(1,time_end+1)
    time_sine = [math.sin(t) for t in time]
    sine = [operating_point + amplitude*y for y in time_sine]
    return sine


def create_bounds_mpc(system_inputs, control_horizon):
    lb = []
    ub = []
    for this_in in system_inputs:
        lb.extend(this_in['lower_bound'] * control_horizon)
        ub.extend(this_in['upper_bound'] * control_horizon)
    return Bounds(lb, ub)


def create_constraints_mpc(constraints, control_horizon):
    a = np.empty(0)
    for this_coeff in constraints['coeffs']:
        to_add = np.diagflat([this_coeff] * control_horizon)
        if not a.any():
            a = to_add
        else:
            a = np.hstack((a, to_add))
    return LinearConstraint(a, [constraints['lower_bound']] * control_horizon,
                            [constraints['upper_bound']] * control_horizon)


def model_predictive_control(model, components, system_inputs, control_horizon, prediction_horizon, minimize_options,
                             bounds, constraints, initial_inputs, sim_params_mpc, i_interval):
    # define system inputs
    # system_inputs = define_system_inputs_mpc()
    # a. constraints definieren
    """
    lb = []
    ub = []
    for this_in in system_inputs:
        lb.extend(this_in['lower_bound'] * control_horizon)
        ub.extend(this_in['upper_bound'] * control_horizon)
    bounds = Bounds(lb, ub)
    if constraints:
        a = np.empty(0)
        for this_coeff in constraints['coeffs']:
            to_add = np.diagflat([this_coeff] * control_horizon)
            if not a.any():
                a = to_add
            else:
                a = np.hstack((a, to_add))
        linear_constraint = LinearConstraint(a, [constraints['lower_bound']] * control_horizon,
                                            [constraints['upper_bound']] * control_horizon)
    """
    # b. Startwerte u_vec_0 vorgeben
    # u_vec_0 = []
    # for i in range(len(initial_inputs)):
    #     u_vec_0.extend([initial_inputs[i]] * control_horizon)
    # c. cost_function_mpc() als nested function definieren
    def cost_function_mpc(u_vec):
        # a. Steuerfolge für Prädiktionshorizont erweitern und
        # b. Iteration durch system_inputs und nacheinander aufteilen und speichern von u_vec in den einzelnen Inputs
        u_vec = u_vec.tolist()
        iter = 0
        for this_in in system_inputs:
            control_data = u_vec[(iter * control_horizon):((iter + 1) * control_horizon)]
            iter = iter + 1
            control_data.extend([control_data[-1]] * (prediction_horizon - control_horizon))
            this_in['mpc_data'] = control_data
        # c. run_model_mpc() aufrufen  Rückgabe: Regelgrößen-Vektoren für Prädiktionshorizont
        # system_outputs, i_interval_break, costs = run_model_mpc(model, components, sim_params_mpc, i_interval, prediction_horizon, system_inputs)
        costs = run_model_mpc(model, components, sim_params_mpc, i_interval, prediction_horizon, system_inputs)
        """
        if not system_outputs:
            cost = 1e12 * (prediction_horizon - i_interval_break + i_interval)**2
            print(prediction_horizon - i_interval_break + i_interval)
        else:
            mass_h2_avl = system_outputs[3]['flow_value']
            # print(mass_h2_avl)
            mass_h2_demand = system_outputs[2]['flow_value']
            power_supply = system_outputs[0]['flow_value']
            power_sink = system_outputs[1]['flow_value']
            mass_h2_supply = system_outputs[4]['flow_value']
            mass_h2_sink = system_outputs[5]['flow_value']
            # x = [y-z for y,z in zip(mass_h2_avl,mass_h2_sink)]
            # print(x)
            # d. Teil-Kostenfunktionen als nested functions definieren
            def cost_function_demand_old(iteration):
                return (mass_h2_avl[iteration] - mass_h2_demand[iteration]) ** 2
            def cost_function_demand(iteration):
                # print('demand_cost')
                # print(mass_h2_avl[iteration] * (-9.5))
                return mass_h2_avl[iteration] * (-9.5)
            def cost_function_supply(iteration):
                # print('supply_cost')
                # print(power_supply[iteration] * 0.0001855)
                return power_supply[iteration] * 0.0001855
            def cost_function_sink(iteration):
                # print('sink_cost')
                # print(power_sink[iteration] * (-0.00004))
                return power_sink[iteration] * (-0.00004)
            def cost_function_supply_h2(iteration):
                # print('supply_h2_cost')
                # print(mass_h2_supply[iteration] * 100)
                return mass_h2_supply[iteration] * 100 # 100 Euro pro kg H2
            def cost_function_sink_h2(iteration):
                # print('sinkh2_cost')
                # print(mass_h2_sink[iteration] * (9.5))
                return mass_h2_sink[iteration] * (9.5)
            def cost_function_electrolyzer(iteration):
                gamma1 = 0.5*1e-6 # 0.0005 # 0.5
                cost_electrolyzer = 0
                if iteration == 0:
                    return 0
                else:
                    for this_in in system_inputs:
                        if this_in['comp_name'] == 'this_ely':
                            cost_electrolyzer = (this_in['mpc_data'][iteration] -
                                                    this_in['mpc_data'][iteration - 1]) ** 2 * gamma1
                    print('ely_cost')
                    print(cost_electrolyzer)
                    return cost_electrolyzer
            # e. Iteration über Prädiktionshorizont:
            # cost = 0
            # for k in range(0, prediction_horizon):
                # cost = cost + cost_function_demand(k) + cost_function_supply(k) + cost_function_sink(k) \
                #        + cost_function_electrolyzer(k) + cost_function_supply_h2(k) + cost_function_sink_h2(k)
                # cost = cost + cost_function_demand(k) + cost_function_supply(k) + cost_function_sink(k) \
                #         + cost_function_supply_h2(k) + cost_function_sink_h2(k)
        # f. Rückgabe der Kosten
        # print('cost-diff')
        # print(cost-costs)
        """
        return costs
    # d. Optimierer aufrufen mit cost_function_mpc()
    # res = minimize(cost_function_mpc, u_vec_0, method='trust-constr', options = {'verbose': 1}, bounds = bounds)
    if constraints:
        res = minimize(cost_function_mpc, initial_inputs, method='trust-constr', options=minimize_options,
                       bounds=bounds, constraints=constraints)
    else:
        res = minimize(cost_function_mpc, initial_inputs, method='L-BFGS-B', options = minimize_options,
                       bounds = bounds)
    # e. system_inputs für den ersten Zeitschritt der optimierten Steuertrajektorie/ für alle Zeitschritte setzen
    iter = 0
    for this_in in system_inputs:
        this_in['mpc_data'] = res.x[(control_horizon * iter): (control_horizon * (iter + 1))]
        iter = iter + 1
    return system_inputs


def run_model_mpc(model, components_init, sim_params, i_interval_start, prediction_horizon, system_inputs):
    # There are no costs yet.
    costs = 0
    # There are no results yet.
    df_results = None
    results_dict = None
    # reset sim_params.i_interval to start value
    sim_params.i_interval = i_interval_start
    # clone model
    components = deepcopy(components_init)
    for this_comp in components:
        this_comp.sim_params = sim_params
    # a. system_outputs leer initialisieren
    system_outputs = []
    # b. Smooth laufen lassen über alle Prädiktionsschritte (import from run_smooth)
    # ------------------- SIMULATION -------------------
    for i_interval in range(i_interval_start, i_interval_start + prediction_horizon):
        # Save the interval index of this run to the sim_params to make it usable later on.
        sim_params.i_interval = i_interval

        # i. Stellgrößen setzen (Wert aus Steuerfolge für aktuellen Prädiktionsschritt)
        # set system_inputs
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
            # raise SolverNonOptimalError('solver status: ' + status +
            #                            " / termination condition: " + termination_condition)
            print('solver status: ' + status +
                 " / termination condition: " + termination_condition)
            # system_outputs = []
            costs = 1e12 * (prediction_horizon - i_interval + i_interval_start)**2
            print(prediction_horizon - i_interval + i_interval_start)
            # return system_outputs, i_interval, costs
            return costs
        else:
            # ------------------- HANDLE RESULTS -------------------
            # Get the results of this oemof run.
            results = processing.results(model_to_solve)
            results_dict = processing.parameter_as_dict(model_to_solve)
            df_results = processing.create_dataframe(model_to_solve)

            # ii. Regelgrößen abgreifen und in Vektor speichern
            # track system outputs for mpc
            # system_outputs = get_system_output_mpc(results,system_outputs)

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
                # add mpc costs after update of flows and states!
                costs += this_comp.mpc_cost_function()

    # d. Rückgabe der Vektoren der Regelgröße über Prädiktionshorizont
    # track system outputs for mpc
    # return system_outputs, i_interval, costs
    print(costs)
    return costs


def remove_trailing_nones_mpc(this_comp, n_intervals, prediction_horizon):
    # the flows, states and results are initialized for n_interval + prediction_horizon which leads to trailing none
    # values after the simulation has finished --> those trailing none values are removed here:
    for this_flow in this_comp.flows:
        this_comp.flows[this_flow] = this_comp.flows[this_flow][:n_intervals - prediction_horizon]
    for this_state in this_comp.states:
        this_comp.states[this_state] = this_comp.states[this_state][:n_intervals - prediction_horizon]
    this_comp.results['variable_costs'] = this_comp.results['variable_costs'][:n_intervals - prediction_horizon]
    this_comp.results['art_costs'] = this_comp.results['art_costs'][:n_intervals - prediction_horizon]
    this_comp.results['variable_emissions'] = this_comp.results['variable_emissions'][:n_intervals - prediction_horizon]

#---------END MPC FUNCTIONS---------------------------------------------------------------------------------------------