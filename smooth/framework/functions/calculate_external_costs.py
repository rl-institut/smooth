import importlib
from smooth.framework.simulation_parameters import SimulationParameters as sp


def calculate_costs_for_external_components(mymodel):

    if mymodel['external_components'] is not None:
        # CHECK IF EXTERNAL COMPONENT NAMES ARE UNIQUE
        # Check if all external component names are unique, otherwise throw an error.
        # Therefore first get all external component names.
        ext_comp_names = []
        for this_ext_comp in mymodel['external_components']:
            ext_comp_names.append(this_ext_comp['name'])

        # Then check if all external component names are unique
        for this_ext_comp_name in ext_comp_names:
            if ext_comp_names.count(this_ext_comp_name) != 1:
                raise ValueError(
                    'External component name "{}" is not unique,'
                    ' please name components unique.'.format(
                        this_ext_comp_name))

        # GET SIMULATION PARAMETERS
        # Create an object with the simulation parameters.
        sim_params = sp(mymodel['sim_params'])

        # CREATE ADDITIONAL COMPONENT OBJECTS
        ext_components = []
        for this_ext_comp in mymodel['external_components']:
            this_ext_comp_name = this_ext_comp['external_component']
            # Add simulation parameters to the components so they can be used
            this_ext_comp['sim_params'] = sim_params
            # Import the module of the component.
            this_comp_module = \
                importlib.import_module('smooth.components.external_component_'
                                        + this_ext_comp_name)
            # While class name is camel case, underscores has to be removed and letters after
            # underscores have to be capital
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

        for this_ext_comp in ext_components:
            this_ext_comp.generate_results()

        return ext_components
