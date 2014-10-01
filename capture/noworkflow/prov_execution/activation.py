# Copyright (c) 2014 Universidade Federal Fluminense (UFF), Polytechnic Institute of New York University.
# This file is part of noWorkflow. Please, consult the license terms in the LICENSE file.

class Activation(object):
    __slots__ = (
        'start', 'file_accesses', 'function_activations',
        'finish', 'return_value', 
        'name', 'line', 'arguments', 'globals',
        'context', 'slice_stack', 'lasti',
        'args', 'kwargs', 'starargs', 
    )
    
    def __init__(self, name, line):
        self.start = 0.0
        self.file_accesses = []
        self.function_activations = []
        self.finish = 0.0
        self.return_value = None
        self.name = name
        self.line = line
        self.arguments = {}
        self.globals = {}
        # Variable context. Used in the slicing lookup
        self.context = {} 
        # Line execution stack. Used to evaluate function calls before execution line 
        self.slice_stack = []
        self.lasti = -1

        self.args = []
        self.kwargs = []
        self.starargs = []
