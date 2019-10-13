import math
import multiprocessing


class OptimizationParameters:
    # The OptimizationParameters class contains all the information needed by the genetic algorithm.
    def __init__(self):
        # PARAMETERS SET BY USER
        # Parameters to run the genetic algorithm (GA).
        self.ga_params = GaParameters()
        # Parameters defining how to vary the model attributes.
        self.attribute_var = []

        # PARAMETERS INTERNAL
        # Number of gens in total [-]
        self.n_gen_total = 0

    def set_params(self, opt_config):
        # Use a configuration file to update the object parameters.

        # Update the GA parameters.
        self.ga_params.set_params(opt_config['ga_params'])
        # Update the attribute variation parameters.
        for this_attribute in opt_config['attribute_variation']:
            self.attribute_var.append(AttributeVariation())
            self.attribute_var[-1].set_params(this_attribute)
            self.n_gen_total += self.attribute_var[-1].n_gen

    def get_attribute_values(self, gen):
        # Get the values from one gen configuration.
        # Parameter:
        #  gen: array of gen byte values.

        # List of the actual values for each attribute.
        attribute_values = []
        # Position counter for index in gen [-].
        gen_pos = 0
        # Loop through all attributes.
        for this_attribute in self.attribute_var:
            # Extract the gen values belonging to this attribute.
            this_gen = gen[gen_pos:gen_pos + this_attribute.n_gen]
            # Update the position on the gen
            gen_pos += this_attribute.n_gen
            # Convert the gen to an integer value [int].
            this_gen_int = self.get_int(this_gen)
            # Get the value for this gen.
            attribute_values.append(this_attribute.get_val(this_gen_int))

        return attribute_values

    def get_int(self, gen):
        # Calculate an integer by a given list of binary values.
        # Parameter:
        #  gen: A gen sequence of binary values [list].

        # Convert the genes to a string and then to an integer.
        binary_string = ''.join((str(this_gen) for this_gen in gen))
        # Return the integer value [int]
        return int(binary_string, 2)


class GaParameters:
    # Attributes needed to run the genetic algorithm.
    def __init__(self):
        # USER DEFINED PARAMETERS
        # Size of the population / number of individuals in the population [-].
        self.population_size = None
        # Number of generations to optimize [-].
        self.n_generation = None
        # Define the number of cores that will be used ('max' will use all cores available) [-].
        self.n_core = 'max'

    def set_params(self, ga_params):
        # Set the parameters for the genetic algorithm defined by the user.
        # Parameter:
        #  ga_params: GA params defined by the user [dict].
        for this_param in ga_params:
            setattr(self, this_param, ga_params[this_param])

        # If as number of cores, max is chosen, use all cores available on this machine.
        if self.n_core == 'max':
            self.n_core = multiprocessing.cpu_count()


class AttributeVariation:
    # Class that contain all information about the attribute that is varied by the genetic algorithm.
    # E.g. the combination val_min = 5, val_max = 60 and val_step = 10 lead to possible values 5, 15, 25, 35, 45 and 55.
    def __init__(self):
        # Name of the component.
        self.comp_name = None
        # Name of the attribute that will be varied.
        self.comp_attribute = None
        # Min. value of the attribute [int/float].
        self.val_min = None
        # Max. value of the attribute [int/float].
        self.val_max = None
        # Step size of the variations of this attribute.
        self.val_step = None

        # INTERNAL PARAMETERS (NOT DEFINED BY USER)
        # Gen number (number of bits each individual has).
        self.n_gen = 0
        # Function that gives the value representation by getting the number of the binary value of the genes.
        self.get_val = None

    def set_params(self, attribute_variation):
        # Set the attributes of this object according to the user input.
        # Parameter:
        #  attribute_variation: parameters defining how to vary the attribute by the GA [dict].
        for this_attr in attribute_variation:
            setattr(self, this_attr, attribute_variation[this_attr])

        self.set_gens()

    def set_gens(self):
        # Convert all attribute variable information into bytes. The bytes will be used as the genes of one individual.
        # Parameters:
        #  attribute_var: Information on all attributes that will be varied [object].

        # Get the number of possible variations for this attribute [-]
        n_step = math.floor((self.val_max - self.val_min) / self.val_step)
        # Get the min. number of bits needed to represent that number [int].
        self.n_gen = math.ceil(math.log(n_step, 2))
        # Define a function that gives back the actual value when the number of the binary genes is given.
        self.get_val = lambda binary_val: min(self.val_min + binary_val * self.val_step, self.val_max)



