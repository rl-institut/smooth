"""Core of smooth.
Solves (M)ILP of an energy system model for discrete time steps using the
Open Energy Modelling Framework solver (`oemof <https://github.com/oemof/oemof-solph>`_).

**********
How to use
**********
:func:`run_smooth` expects an energy model. Such a model consists of

* energy sources
* energy sinks
* energy transformers
* buses to transport energy

Additionally, simulation parameters are needed to run the model.
A model is  therefore defined as a dictionary containing all *components*,
buses (grouped as *busses*) and simulation parameters (grouped as *sim_params*,
see :class:`smooth.framework.simulation_parameters.SimulationParameters`).

Example::

    {
        components: {
            name_of_first_component: {
                component: ...,
                capex: ...,
                opex: ...,
                ...
            },
            ...
        },
        busses: [
            name_of_first_bus,
            name_of_second_bus,
            ...
        ],
        sim_params: {
            start_date: ...,
            n_intervals: ...,
            interval_time: ...,
            interest_rate: 0.03,
            ...
        }
    }

.. note::
    Legacy models (version < 0.2.0) define their components as a list
    with an extra field *name* for each component. This is deprecated.

******
Result
******
Two items are returned. The second is a string describing the oemof solver return status.
You want this to be 'ok', although `other values are possible
<http://www.pyomo.org/blog/2015/1/8/accessing-solver>`_.
The first item returned is a list of all components, each updated with

- sim_params: the original simulation parameters, plus *date_time_index* \
    for each time step and *sim_time_span* in minutes
- results: results from the simulation

    - variable_costs*
    - art_costs*
    - variable_emissions*
    - annuity_capex
    - annuity_opex
    - annuity_variable_costs
    - annuity_total
    - annual_fix_emissions
    - annual_op_emissions
    - annual_variable_emissions
    - annual_total_emissions
- states: dictionary with component-specific attributes.\
    Each entry is a list with values for each time step
- flows: dictionary with each flow of this component.\
    Key is tuple (from, to), entry is list with value for each time step
- data: pandas dataframe
- (component-specific attributes)

\\* a list with a value for each time step

**************
Implementation
**************
:func:`run_smooth` has three distinct phases:
initialization, simulation and post processing.

Initialization
--------------
Not much to see here. Mainly, component instances get created from the model description.
For legacy models (version < 0.2.0), the component list is converted to a dictionary.
No oemof model is built here.

Simulation
----------
The main part of the function. For each time step, an oemof model is solved and evaluated:

#. print current time step to console if *print_progress* is set in parameters
#. initialize oemof energy system model
#. create buses
#. update components and add them to the oemof model
#. update bus constraints
#. write lp file in current directory
#. call solver for model
#. check returned status for non#.optimal solution
#. handle results for each component

    #. update flows
    #. update states
    #. update costs
    #. update emissions

Post-processing
---------------
After all time steps have been computed, call the *generate_results* function of each component.
Finally, return the updated components and the last oemof status.
"""

from oemof import solph
from oemof.outputlib import processing
from smooth.framework.simulation_parameters import SimulationParameters as sp
from smooth.framework.functions.debug import get_df_debug, show_debug, save_debug
from smooth.framework.exceptions import SolverNonOptimalError
from smooth.framework.functions.functions import create_component_obj
import pandas as pd


def run_smooth(model):
    """Run the smooth simulation framework

    :param model: smooth model object containing parameters for components, simulation and busses
    :type model: dictionary
    :return: results of all components and oemof status
    :rtype: tuple of components and string
    :raises: *SolverNonOptimalError* if oemof result is not ok and not optimal
    """

    # ------------------- INITIALIZATION -------------------
    # legacy: components may be list. Convert to dict.
    if isinstance(model["components"], list):
        names = [c.pop("name") for c in model["components"]]
        model.update({'components': dict(zip(names, model["components"]))})

    # GET SIMULATION PARAMETERS
    # Create an object with the simulation parameters.
    sim_params = sp(model['sim_params'])

    # CREATE COMPONENT OBJECTS
    components = create_component_obj(model, sim_params)

    # There are no results yet.
    df_results = None
    results_dict = None

    # ------------------- SIMULATION -------------------
    for i_interval in range(sim_params.n_intervals):
        # if i_interval == 96:
        #     sim_params.mpc_flag = True
        # Save the interval index of this run to the sim_params to make it usable later on.
        sim_params.i_interval = i_interval
        if sim_params.print_progress:
            print('Simulating interval {}/{}'.format(i_interval+1, sim_params.n_intervals))

        # Initialize the oemof energy system for this time step or for the control horizon in mpc-case
        this_time_index = sim_params.date_time_index[i_interval: (i_interval + 1)]
        if sim_params.mpc_flag:
            date_time_index = pd.date_range(
                this_time_index[0], periods=sim_params.mpc_control_horizon,
                freq='{}min'.format(sim_params.interval_time))
            oemof_model = solph.EnergySystem(timeindex=date_time_index)
        else:
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
                df_debug = get_df_debug(df_results, results_dict, new_df_results, i_interval)
                show_debug(df_debug, components)
            raise SolverNonOptimalError('solver status: ' + status +
                                        " / termination condition: " + termination_condition)

        if i_interval > 0:#sim_params.show_debug_continuous_flag:
            new_df_results = processing.create_dataframe(model_to_solve)
            df_debug = get_df_debug(df_results, results_dict, new_df_results, i_interval)
            save_debug(df_debug, components, i_interval)

        # ------------------- HANDLE RESULTS -------------------
        # Get the results of this oemof run.
        results = processing.results(model_to_solve)
        if sim_params.show_debug_flag:
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
    # if sim_params.mpc_flag:
    #     return results, results_dict, df_results
    # Calculate the annuity for each component.
    for this_comp in components:
        this_comp.generate_results()

    return components, status
