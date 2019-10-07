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
### Installation of SMOOTH 
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

















