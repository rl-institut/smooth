~~~~~~~~~~~~~~~
Getting started
~~~~~~~~~~~~~~~

SMOOTH stands for "Simulation Model for Optimized Operation and Topology of Hybrid energy systems", and this
tool serves to minimise costs and maximise the sustainability of dynamic energy systems. The key features 
of SMOOTH are:

* The real world energy system is reduced to its relevant components
* Detailed modelling of components including:

  * Non-linear component behaviour
  * State-dependant component behaviour
  * Tracking arbitrary states of component 

* Stepwise simulation without using perfect foresight
* Parameter optimization possible in combination with a genetic algorithm


.. contents::
    :depth: 1
    :local:
    :backlinks: top


Documentation
=============

Full documentation can be found soon.

Installing smooth
=================

In order to use SMOOTH, the smooth package and its requirements need to be installed.

.. code:: bash

    pip install -r requirements.txt
    python setup.py install


You also need to install the solver for oemof. This can be done according to
`this <https://oemof.readthedocs.io/en/stable/installation_and_setup.html#installation-and-setup-label>`_
documentation page.


Structure of the SMOOTH module
==============================

The SMOOTH module consists of four sections: components, examples, framework and optimization. 

Components
==========
The :ref:`smooth.components package` contains all of the existing components of an energy
system that have already been built in SMOOTH, along with any related functions. Input parameters
that are defined by the user in the model definition, or default values that are specified within
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
Click on the above links to see how the simulation works. 

Optimization
============


Got further questions on using SMOOTH?
======================================

Contact ...


License
=======

SMOOTH is licensed under the Apache License, Version 2.0 or the MIT license, at your option.
See the `COPYRIGHT file <https://github.com/rl-institut/smooth/blob/dev/COPYRIGHT>`_ for details.
