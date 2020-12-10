~~~~~~~~~~~~~~~
Getting started
~~~~~~~~~~~~~~~

SMOOTH stands for "Simulation Model for Optimized Operation and Topology of Hybrid energy systems". This
tool serves to minimise costs and maximise the sustainability of dynamic energy systems. The key features 
of SMOOTH are:

* The real world energy system is reduced to its relevant components
* Detailed modelling of components including non-linear component behaviour, state-dependent component behaviour
  and tracking arbitrary states of the components 
* Stepwise simulation without using perfect foresight
* Parameter optimization possible in combination with a genetic algorithm


.. contents::
    :depth: 1
    :local:
    :backlinks: top


Documentation
=============

Full documentation can be found `here <https://smooth.readthedocs.io/en/latest/>`_

Installing smooth
=================

In order to use SMOOTH, the smooth package and its requirements need to be installed. There
is the option to clone the current repository of SMOOTH to your local machine using:

.. code:: bash

	git clone https://github.com/rl-institut/smooth

The necessary requirements (found in requirements.txt in repository) are installed into a
working Python3 environment by: 

.. code:: bash

    pip install -r requirements.txt
	
SMOOTH is then installed by:

.. code:: bash

    python setup.py install


You also need to install the solver for oemof. This can be done according to
`this <https://oemof-solph.readthedocs.io/en/latest/readme.html#installing-a-solver>`_
documentation page.


Structure of the SMOOTH module
==============================

The SMOOTH module consists of four sections: components, examples, framework and optimization. 

Components
==========
The :ref:`smooth.components package` contains all of the existing components of an energy
system that have already been built in SMOOTH, along with any related functions. Input parameters
that are defined by the user in the model definition, or by default values that are specified within
the component, are used to calculate and determine the behaviour of the component for each timestep.  
Within each component, an oemof component is created using the parameters defined or 
calculated in the SMOOTH component to be used later in the oemof model. Visit the section for 
detailed information on each of the components and how to build a new component. 

Examples
========
In order to get a better, applied understanding of how to define a model, and either run a simulation
or an optimization, see the `examples directory <https://github.com/rl-institut/smooth/tree/dev/smooth/examples>`_ 
for examples, and the :ref:`smooth.examples package` section for corresponding explanations.

Framework
=========
The :ref:`smooth.framework package` consists of the main function that runs the SMOOTH simulation
framework (the :func:`run_smooth` function) as well as other functions that are necessary for 
updating and evaluating the simulation results (in the :ref:`smooth.framework.functions package`).
An outline and brief description of the available functions in the framework is presented below:

* :func:`~smooth.framework.run_smooth`: the main function which enables the simulation in SMOOTH, 
  and must be called by the user.
* :func:`~smooth.framework.functions.calculate_external_costs`: calculates costs for components 
  in the system which are not part of the optimization but their costs should be taken into 
  consideration. This function can be called in the same file as the run_smooth function. 
* :func:`~smooth.framework.functions.debug`: generates debugging information from
  the results, and prints, plots and saves them. It is called in the run_smooth function if the 
  user sets the *show_debug_flag* parameter as True in the simulation parameters.
* :func:`~smooth.framework.functions.load_results`: loads the saved results of either a 
  simulation or optimization. Can be called by the user in a file where the results are 
  evaluated.
* :func:`~smooth.framework.functions.plot_interactive_results`: plots interactive results of a
  SMOOTH run, which can be called after the simulation/optimization results are obtained.
* :func:`~smooth.framework.functions.plot_results`: plots results of a SMOOTH run, which can 
  be called after the simulation/optimization results are obtained.
* :func:`~smooth.framework.functions.print_results`: prints the financial results of a 
  SMOOTH run, which can be called after the simulation/optimization results are obtained.
* :func:`~smooth.framework.functions.save_important_parameters`: saves the most important
  parameters from the optimization results in a CSV file, automatically generates pie plots
  of certain results and saves all of the flows in a dataframe. Can be called in a file
  where the results are evaluated.
* :func:`~smooth.framework.functions.save_results`: saves the results of either a SMOOTH
  run or an optimization, which can be called after the results are obtained.
* :func:`~smooth.framework.functions.update_annuities`: calculates and updates the financial
  and emission annuities for the components used in the system. It is called in the 
  generic Component class, which is used to define each component.
* :func:`~smooth.framework.functions.update_fitted_costs`: calculates the fixed costs and
 fixed emissions of a component. The user can define the dependencies on certain values 
 using a set of specific fitting methods. This function is also called in the generic 
 Component class, which is used to define each component.

Optimization
============
The genetic algorithm used for the optimization in SMOOTH is defined in the 
:ref:`smooth.optimization package`, along with instructions on how to use it.

Got further questions on using SMOOTH?
======================================

Contact ...


License
=======

SMOOTH is licensed under the Apache License, Version 2.0 or the MIT license, at your option.
See the `COPYRIGHT file <https://github.com/rl-institut/smooth/blob/dev/COPYRIGHT>`_ for details.
