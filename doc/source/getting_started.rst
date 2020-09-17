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

In order to use SMOOTH, the smooth package needs to be installed.

Installation of oemof (specific version required)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Further, oemof has to be installed.
While some smooth components are described by non-linear component behaviour, the oemof component
PiecewiseLinearTransformer is needed. This component is currently in the review process, therefore
the pull request containing this component needs to be downloaded from github directly and installed
locally. This can be done by the following steps:

1. Clone `oemof <https://github.com/oemof/oemof-solph>`_ to your local machine

.. code:: bash

    git clone https://github.com/oemof/oemof-solph.git

2. In the oemof repo, fetch the pull request version `#592 <https://github.com/oemof/oemof-solph/pull/592>`_ ,
which contains the component, to a new branch BRANCHNAME of your choice.

.. code:: bash

    git fetch origin pull/592/head:BRANCHNAME

3. Checkout the branch BRANCHNAME of the pull request version.

.. code:: bash

    git checkout BRANCHNAME

4. Install the pull request version of oemof with pip

.. code:: bash

    pip install .

5. Install the solver for oemof (if you wasn't running oemof before). This can be done according to
`this <https://oemof.readthedocs.io/en/stable/installation_and_setup.html#installation-and-setup-label>`_
documentation page.


Structure of the SMOOTH module
==============================

The SMOOTH module consists of four sections: components, examples, framework and optimization. 

Components
==========
The :ref:`smooth.components package` section contains all of the existing components of an energy
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
