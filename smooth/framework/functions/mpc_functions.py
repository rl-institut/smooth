import pandas as pd
from oemof.outputlib import views
from oemof import solph
from oemof.outputlib import processing


#--------------------MPC FUNCTIONS--------------------------------------------------------------------------------------
def run_mpc_dummy(this_model,components,system_outputs,iteration):
    # function calculating the system inputs (control variables) based on the system outputs
    # (controlled process variables) and a (dummy) mpc algorithm

    # system outputs
    # check if system_outputs is empty
    if not system_outputs:
        # set initial values
        system_outputs = define_system_outputs_mpc()

    # system inputs
    system_inputs = define_system_inputs_mpc() # auslagern und Aufruf in run_smooth???!!!
    system_inputs['power_electrolyzer']['mpc_data'] = 0.85
    system_inputs['mflow_h2_storage']['mpc_data'] = step_input_mpc(0,0.1,iteration) # 0.50
    for this_in in system_inputs:
        # Loop through all components of the model dict until the right component is found.
        for this_comp in components:
            if this_comp.name == system_inputs[this_in]['comp_name']:
                # idx = this_model['components'].index(this_comp)
                setattr(this_comp,'mpc_data',system_inputs[this_in]['mpc_data'])
    return


def get_system_output_mpc(results,results_dict,df_results):
    # function tracking the system outputs and returning them for use in run_mpc_dummy
    # system outputs are defined in an auxiliary function
    system_outputs = define_system_outputs_mpc()
    # loop through all system outputs and get the current flow values
    for this_out in system_outputs:
        this_comp_node = views.node(results, this_out['node1_name'])
        this_df = this_comp_node['sequences']
        for i_result in this_df:
            # check if i_result is the desired flow
            # oemof-Doku zu outputlib: flow-keys: (node1,node2); node-keys: (node,None)
            if i_result[0][0] == this_out['node1_name'] and i_result[0][1] == this_out['node2_name']:
                # flow from node1 to node2
                this_out['flow_value'] = this_df[i_result][0]
                # print(this_out['flow_value'])
    return system_outputs


def define_system_inputs_mpc():
    # define the system inputs of your MIMO System
    electrolyzer = {
        'comp_name': 'this_ely',
        'mpc_data': 0
    }
    h2_storage = {
        'comp_name': 'h2_storage_lp',
        'mpc_data': 0
    }
    system_inputs = {'power_electrolyzer': electrolyzer, 'mflow_h2_storage': h2_storage}
    return system_inputs


def define_system_outputs_mpc():
    # define the system outputs of your MIMO System
    supply_el = {
        'node1_name': 'from_grid',
        'node2_name': 'bel',
        'flow_value': 0,
    }
    sink_el = {
        'node1_name': 'bel',
        'node2_name': 'to_grid',
        'flow_value': 0,
    }
    to_demand_h2_mp = {
        'node1_name': 'bh2_mp',
        'node2_name': 'h2_demand_mp',
        'flow_value': 0,
    }
    system_outputs = [supply_el,sink_el,to_demand_h2_mp]
    # To Do: initialize flow values with NaN and set starting values only when requested when the method is called
    return system_outputs


def step_input_mpc(operating_point,step_size,iteration):
    # function returning the current value of a step signal
    # start in operation point, step up and down with specified step size
    step = [operating_point]*5+[operating_point+step_size]*5+[operating_point-step_size]*5+[operating_point]*9
    # TO DO: an beliebige Simulationszeiträume anpassen
    return step[iteration]


def cost_function_mpc(this_model,components,system_inputs,u_vec,prediction_horizon,sim_params):
    for this_in in system_inputs:
        # Loop through all components of the model dict until the right component is found.
        for this_comp in this_model['components']:
            if this_comp['name'] == this_in['comp_name']:
                idx = this_model['components'].index(this_comp)
                setattr(components[idx],this_in['comp_attribute'],u_vec[this_in])
    # Frage: oemof modell kann für beliebig viele Zeitschritte eine Vorgabe der Fixed Flows bekommen!!?
    # also kann ich direkt die gesamte Steuertrajektorie in das eine oemof-modell zu dem Zeitpunkt geben?!!
    # gesamte Steuertrajektorie: u1 = u1,0 u1,1 ... u1,(control_horizon-1), u1,(control_horizon), u1,(control_horizon),
    # ...,u1,(control_horizon) --> Anzahl der Einträge: prediction_horizon
    system_outputs = run_model_mpc(this_model,components,sim_params, prediction_horizon)
    return


def run_model_mpc(this_model,components,sim_params, prediction_horizon):
    # Initialize the oemof energy system for a number of timesteps according to the prediction horizon
    date_time_index = pd.date_range('1/1/2012', periods=prediction_horizon,
                                    freq='{}min'.format(sim_params.interval_time)) # freq = 'H' --> Stündlich? Vorerst ok, aber was muss man machen, um das zu ändern?
     # i_interval brauchen wir nicht mehr, wir starten bei Null (mit Anfangswerte sind system_outputs bei i_interval)
    oemof_model = solph.EnergySystem(timeindex=date_time_index)

    # ------------------- CREATE THE OEMOF MODEL FOR THIS INTERVAL -------------------
    # Create all busses and save them to a dict for later use in the components.
    busses = {}

    for i_bus in this_model['busses']:
        # Create this bus and append it to the "busses" dict.
        busses[i_bus] = solph.Bus(label=i_bus)
        # Add the bus to the simulation model.
        oemof_model.add(busses[i_bus])
    # vielleicht busse im run_smooth erstellen lassen und übergeben!

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

    # brauchen wird das hier?
    # if i_interval == 0:
    #     # Save the set of linear equations for the first interval.
    #     model_to_solve.write('./oemof_model.lp', io_options={'symbolic_solver_labels': True})

    oemof_results = model_to_solve.solve(solver='cbc', solve_kwargs={'tee': False})

    # später anschauen, ob und wie das hier sinnvoll ist
    # # ------------------- CHECK IF SOLVING WAS SUCCESSFUL -------------------
    # # If the status and temination condition is not ok/optimal, get and
    # # print the current flows and status
    # status = oemof_results["Solver"][0]["Status"].key
    # termination_condition = oemof_results["Solver"][0]["Termination condition"].key
    # if status != "ok" and termination_condition != "optimal":
    #     if sim_params.show_debug_flag:
    #         new_df_results = processing.create_dataframe(model_to_solve)
    #         df_debug = get_df_debug(df_results, results_dict, new_df_results)
    #         show_debug(df_debug, components)
    #     raise SolverNonOptimalError('solver status: ' + status +
    #                                 " / termination condition: " + termination_condition)

    # ------------------- HANDLE RESULTS -------------------
    # Get the results of this oemof run.
    results = processing.results(model_to_solve)
    # results_dict = processing.parameter_as_dict(model_to_solve)
    # df_results = processing.create_dataframe(model_to_solve)

    # track system outputs for mpc
    return get_system_output_mpc(results)


#---------END MPC FUNCTIONS---------------------------------------------------------------------------------------------