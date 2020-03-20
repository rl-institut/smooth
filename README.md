# SMOOTH - Simulation Model for Optimized Operation and Topology of Hybrid energy systems

## Features
The python simulation framework smooth allows modelling energy systems and optimizing their behaviour.
The key features of smooth are:

* Detailed modelling of components
    * Non-linear component behaviour
    * State-dependant component behaviour
    * Tracking arbitrary states of component
* Stepwise simulation without using perfect foresight
* Parameter optimization possible in combination with genetic algorithm

## Usage of oemof
While the components and the algorithm executing the simulation are part of SMOOTH, each component
creates a valid oemof model for each time step and this system is solved by oemof.

For more information to oemof, see [here](https://github.com/oemof/oemof)

## Installation
### Installation of smooth
In order to use SMOOTH, the smooth package needs to be installed.

### Installation of oemof (specific version required)
Further, oemof has to be installed.
While some smooth components are described by non-linear component behaviour, the oemof component
PiecewiseLinearTransformer is needed. This component is currently in the review process, therefore
the pull request containing this component needs to be downloaded from github directly and installed
locally. This can be done by the following steps:

1. Clone [oemof](https://github.com/oemof/oemof) to your local machine
    ```
    git clone https://github.com/oemof/oemof.git
    ```
2. In the oemof repo, fetch the pull request version [#592](https://github.com/oemof/oemof/pull/592),
which contains the component, to a new branch BRANCHNAME of your choice.
    ```
    git fetch origin pull/592/head:BRANCHNAME
    ```
3. Checkout the branch BRANCHNAME of the pull request version.
    ```
    git checkout BRANCHNAME
    ```
4. Install the pull request version of oemof with pip
    ```
    pip install .
    ```
5. Install the solver for oemof (if you wasn't running oemof before). This can be done according to
[this](https://oemof.readthedocs.io/en/stable/installation_and_setup.html#installation-and-setup-label)
documentation page.

## Framework Functions
The following functions can be used directly for the framework. Next to running smooth or an optimization, there are
functions to print results, plot results and to save or load results. The following gives a brief description:

### run_smooth

### run_optimization

### load_results

### save_results

### print_smooth_results

### plot_smooth_results

### plot_optimization_results


## Simulation Model


## Components


### Base Parameters
Each component inherits from the base component (component.py). This way, each component gets the following attributes:
* component: Type of the component [string]
* name: Name of this component (must be unique) [sting]
* life_time: Life time of the component (only required if CAPEX are given) [a]
* sim_params: Simulation parameters (like interval time) [object]
* results: Here result values are saved like variable costs and annuities [dict]
* states: Here states are saved [dict]
* variable_costs:
* artificial_costs:
* opex:
* capex:
* fs_component_name:
* fs_attribute_name:

### Artificial Costs
oemof always solves the system by minimizing the costs. To be able to control the system behaviour in a certain way, a
concept called artificial costs is introduced. Those costs are defined in the components and are used in the oemof
model (and therefore have an effect on the cost minimization). But while they are only used to control the system and
are no real costs, they are not used in the financial evaluation at the end of the simulation.

### Foreign States
Some components behaviour is dependant on so called foreign states, that is a state or attribute of another component
(e.g. the artificial costs of the electricity grid can be dependant on a storage state of charge in order to fill
the storage with grid electricity when the storage is below a certain threshold). While the effect of the foreign states
is determined in the component itself, the mechanics on how to define the foreign states is the same for each component.
Foreign states are always defined by the attributes:
* fs_component_name: String (or list of strings for multiple foreign states) of the foreign component.
* fs_attribute_name: String (or list of strings for multiple foreign states) of the attribute name of the component.

If a fixed value should be used as a foreign state, here fs_component_name has to be set to None and fs_attribute_name
has to be set to the numeric value.

## Financials
The costs and revenues are tracked for each component individually. They can be divided in variable costs and
CAPEX and OPEX. The variable costs are costs that depend on the operation of a component, for example the
amount of electricity a grid supplies. The CAPEX and OPEX are defined by the model parameters. CAPEX are
one time investment costs (in EUR) and OPEX are annual operation costs (in EUR/a).

After the simulation, all costs and revenues are transferred to annuities (yearly costs in EUR/a). This way,
the costs can be mixed together and different models of different simulations times can be compared.

### Variable Costs
Variable costs are costs that are dependant on the operation of a component (e.g. fuel or electricity costs).

### CAPEX and OPEX
Next to variable costs, each component can have one time investment costs (CAPEX) and annual operation
costs (OPEX). Those costs can be set by the parameters "opex" and "capex", both being dictionaries.
Both dictionaries can have the following key values:

* *cost*: can be set directly with key set to "fix", otherwise the cost are calculated dependant on
    *dependant_value*
* *key*: defines how the costs should be calculated, a description in more detail can be found below
* *dependant_value*: string of the component parameter the cost value depends on
* *fitting_value*: for the keys "exp", "poly" and "free" fitting values are needed to calculate the costs

After the calculations, the units of CAPEX are always EUR and the unit of OPEX are always EUR/a.

#### Fitting Methods
The fitting method of the cost is chosen by the key. The different fitting methods are:
* fix: No fitting is done, the value given as *cost*. The *cost* value for CAPEX is taken in EUR while the
    cost value for OPEX is taken in EUR/a.
    ```
    cost = cost
    ```
* spec: Specific cost that are dependant on one component parameter (e.g. EUR/kW) are given. The value of
*dependant_value* is a string of the parameter name (e.g. "power_max"). *fitting_value* is multiplied with
    the value of the parameter to get the costs:
    ```
    cost = fitting_value * component[dependant_value]
    ```
    As one special case, as *dependant_value* for the OPEX calculation, "capex" can be choosen. In that case,
    the fitting value is multiplied with the CAPEX, which are calculated before the OPEX (as an example, if
    *dependant_value* = "capex" and *fitting_value* = 0.04, the OPEX will be 4 % of the CAPEX in EUR/a).

    Another special case is choosing "cost" as *fitting_value*, that way the current cost value is used as
    fitting value.
* exp: Exponential fitting of the costs. A list of two or three entries can be given as *fitting_value*, the
    costs are calculated in the following way:
    ```
    for two fitting values [fv_1, fv_2]:
    cost = fv_1 * exp(dependant_value * fv_2)

    for three fitting values [fv_1, fv_2, fv_3]:
    cost = fv_1 + fv_2 * exp(dependant_value * fv_3)
    ```
* poly: Polynomial fitting, where an arbitrary amount of fitting values can be given as a lig. The costs are
    calculated like:
    ```
    for an arbitrary number of fitting values [fv_1, fv_2, fv_3, ..., fv_n]
    cost = fv_1 + fv_2 * dependant_value**1 + fv_3 * dependant_value**2 + ... + fv_n * dependant_value**(n-1)
    ```
* free: Like the polynomial fitting, but here the exponents can be chosen freely. As *fitting_values*, a list
    with an even number of fitting values has to be given. The costs are calculated like:
    ```
    for an even number of fitting values [fv_1, fv_2, fv_3, ..., fv_n]
    cost = fv_1 * dependant_value**fv_2 + fv_3 * dependant_value**fv_4 + ... + fv_(n-1) * dependant_value**fv_n
    ```

### Financial Results
In order to make the variable costs, CAPEX and OPEX comparable, once the simulation is done, annuities are
calculated. To get an annuity, the following steps have to be done:

* variable costs: The variable costs of one component are summed up and represent the costs or revenues generated
in the simulation period. To get a yearly payment or revenue, the values for simulation times other than one year
have to be corrected by that time.
    ```
    var_cost_annuity = sum(var_cost) * 365_days / simulated_days
    ```
* CAPEX: To derive an annuity, the one time investment or CAPEX have to be transferred by taking into account the
life time (lt) of the component and the interest rate (ir). The equation is shown in the following:
    ```
    capex_annuity = capex * (ir * (1 + ir)**lt) / (((1 + ir)**lt) - 1)
    ```
* OPEX: The OPEX are already yearly costs and don't have to be transformed.


## Optimization

In smooth, there is a build in support for optimization component parameters with a genetic algorithm, the Python
package [*deap*](https://deap.readthedocs.io/en/master/) is used for that. The following gives an overview on how to set
up a smooth optimization run.

### Optimization Parameters











