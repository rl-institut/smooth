~~~~~~~~~~~~~~~
Getting started
~~~~~~~~~~~~~~~

SMOOTH stands for "Simulation Model for Optimized Operation and Topology of Hybrid energy systems"


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


Structure of the smooth module
==============================

Componentes, Framework, ...


Examples
========

See the `examples directory <https://github.com/rl-institut/smooth/tree/dev/smooth/examples>`_ for examples.



Got further questions on using SMOOTH?
======================================

Contact ...


License
=======

SMOOTH is licensed under the Apache License, Version 2.0 or the MIT license, at your option.
See the `COPYRIGHT file <https://github.com/rl-institut/smooth/blob/dev/COPYRIGHT>`_ for details.
