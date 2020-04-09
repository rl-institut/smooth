.. _smooth_components_label:

~~~~~~~~~~~~~~~~~
Smooth components
~~~~~~~~~~~~~~~~~

Description on the smooth components

.. contents::
    :depth: 2
    :local:
    :backlinks: top


How to build up an energy system model using the smooth components?
-------------------------------------------------------------------

See the example.
See :ref:`smooth_components_list_label` for a list of all components.

Set up an energy system
^^^^^^^^^^^^^^^^^^^^^^^

See the example. Configure the json file.


Add components to the energy system
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

See example. Define the components. You also need to define buses. The underlying oemof components, buses and flows are created automatically.

Component
+++++++++

Bus
+++

Flow
++++





.. _smooth_optimise_es_label:

Optimise your energy system
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the genetic algorithm.

Analysing your results
^^^^^^^^^^^^^^^^^^^^^^

Use the plot_results and save_results functions.


.. _smooth_components_list_label:

Smooth components
-----------------

 * :ref:`smooth_components_electrolyzer_label`

 * :ref:`smooth_components_compressor_label`

.. _smooth_components_electrolyzer_label:

Electrolyzer (alkaline)
^^^^^^^^^^^^^^^^^^^^^^^

Descriptions on the electrolyzer component:

.. autoclass:: smooth.components.component_electrolyzer.Electrolyzer
    :members:
    :undoc-members:
    :show-inheritance:


.. _smooth_components_compressor_label:

Compressor (hydrogen)
^^^^^^^^^^^^^^^^^^^^^

Descriptions on the hydrogen compressor component:

.. autoclass:: smooth.components.component_compressor_h2.CompressorH2
    :members:
    :undoc-members:
    :show-inheritance:


.. _smooth_components_examples_label:

Smooth Examples
---------------

See the `example repository <https://github.com/rl-institut/smooth/tree/master/smooth/examples>`_ for examples.
