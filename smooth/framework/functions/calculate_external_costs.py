import importlib
from smooth.framework.simulation_parameters import SimulationParameters as sp


def calculate_costs_for_external_components(model):
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

    ext_components = []
    if type(model) == list:
        ext_comp_names = [comp['name'] for comp in model]
    elif type(model) == dict:
        ext_comp_names = model.keys()
    else:
        raise "Model is neither list nor dictionary. Can't get component names."

    for this_ext_comp in model.get('external_components', []):
        # ENSURE EXTERNAL COMPONENT NAME IS UNIQUE
        this_ext_comp_name = this_ext_comp['name']
        if this_ext_comp_name in ext_comp_names:
            raise ValueError(
                'External component name "{}" is not unique,'
                ' please name components unique.'.format(this_ext_comp_name))
        else:
            ext_comp_names.append(this_ext_comp_name)

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
