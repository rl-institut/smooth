import importlib
from smooth.framework.simulation_parameters import SimulationParameters as sp


def costs_for_ext_components(model):
    """Calculates costs for components in the system which are not to be
    included in the optimization but their costs must still be taken into consideration.
    The name of an external component must be unique within the model.

    :param model: smooth model
    :type model: dictionary
    :return: external components
    :rtype: list of :class:`~smooth.components.component.Component`
    :raises ValueError: an external component name is not unique within the model
    """

    # GET SIMULATION PARAMETERS
    # Create an object with the simulation parameters.
    sim_params = sp(model['sim_params'])

    # get all component names to compare against
    components = model.get('components', [])
    ext_components = []
    if type(components) == list:
        comp_names = [comp['name'] for comp in components]
    elif type(components) == dict:
        comp_names = list(components.keys())
    else:
        raise "Components are neither list nor dictionary. Can't get component names."

    for this_ext_comp in model.get('external_components', []):
        # ENSURE EXTERNAL COMPONENT NAME IS UNIQUE
        this_ext_comp_name = this_ext_comp['name']
        if this_ext_comp_name in comp_names:
            raise ValueError(
                'External component name "{}" is not unique,'
                ' please name components unique.'.format(this_ext_comp_name))
        else:
            comp_names.append(this_ext_comp_name)

        this_ext_comp_name = this_ext_comp['external_component']
        # Add simulation parameters to the components so they can be used
        this_ext_comp['sim_params'] = sim_params
        # Import the module of the component.
        importpath = 'smooth.components.external_component_{}'.format(this_ext_comp_name)
        this_comp_module = importlib.import_module(importpath)
        # class name: camel case
        # remove underscores, letters after underscores have to be capital
        # all caps is special (use as-is)
        class_name = ''
        if this_ext_comp_name.isupper():
            class_name = this_ext_comp_name
        else:
            this_comp_name_split = this_ext_comp_name.split('_')
            for this_comp_name_part in this_comp_name_split:
                class_name += this_comp_name_part.capitalize()
        # Load the class (which by convention has a name with a capital first letter
        # and camel case).
        this_comp_class = getattr(this_comp_module, class_name)
        # Initialize the component.
        this_comp_obj = this_comp_class(this_ext_comp)
        # Check if this component is valid.
        this_comp_obj.check_validity()
        # Add this component to the list containing all components.
        ext_components.append(this_comp_obj)

    # after all external components have been created and validated, generate results
    for this_ext_comp in ext_components:
        this_ext_comp.generate_results()

    return ext_components


def print_ext_components(ext_components):
    """Print the financial results of a smooth run.

    :param ext_components: result from costs_for_ext_components() containing all external components
    :type ext_components: list of :class:`~smooth.components.component.Component`
    """

    # Calculate the sum of all total annuities [EUR/a] and annual emissions [kg/a].
    sum_of_tot_annuity = 0
    sum_of_tot_ann_emission = 0

    print("\n++++++++")
    print('External Components:')
    print("++++++++\n")
    print('{:20s} {:20s} {:20s} {:20s} {:20s} {:20s} {:20s}'.format(
        'component name', 'annutiy capex', 'annuity opex', 'annuity total',
        'annual fix GGE', 'annual op. GGE', 'annual total GGE'
    ))

    for this_comp in ext_components:
        # Print the annuity costs for each component.
        print('{:20s} {:<20d} {:<20d} {:<20d} {:<20d} {:<20d} {:<20d}'.format(
            this_comp.name,
            int(this_comp.results['annuity_capex']),
            int(this_comp.results['annuity_opex']),
            int(this_comp.results['annuity_total']),
            int(this_comp.results['annual_fix_emissions']),
            int(this_comp.results['annual_op_emissions']),
            int(this_comp.results['annual_total_emissions'])
        ))
        # print('Comp: {}: flow: {}'.format(this_comp.name, this_comp.flows))
        # print('Comp: {}: states: {}'.format(this_comp.name, this_comp.states))
        # print('Comp: {}: results: {}'.format(this_comp.name, this_comp.results))

        sum_of_tot_annuity += this_comp.results['annuity_total']
        sum_of_tot_ann_emission += this_comp.results['annual_total_emissions']

    print('\nSum of total annuity is {} EUR/a'.format(int(sum_of_tot_annuity)))
    print('\nSum of total annual emission is {} kg/a'.format(int(sum_of_tot_ann_emission)))
