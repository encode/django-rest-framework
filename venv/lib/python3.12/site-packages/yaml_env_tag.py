""" A custom YAML tag for referencing environment variables in YAML files. """
__version__ = '1.1'

import os
import yaml
from typing import Any


def construct_env_tag(loader: yaml.Loader, node: yaml.Node) -> Any:
    """Assign value of ENV variable referenced at node."""
    default = None
    if isinstance(node, yaml.nodes.ScalarNode):
        vars = [loader.construct_scalar(node)]
    elif isinstance(node, yaml.nodes.SequenceNode):
        child_nodes = node.value
        if len(child_nodes) > 1:
            # default is resolved using YAML's (implicit) types.
            default = loader.construct_object(child_nodes[-1])
            child_nodes = child_nodes[:-1]
        # Env Vars are resolved as string values, ignoring (implicit) types.
        vars = [loader.construct_scalar(child) for child in child_nodes]
    else:
        raise yaml.constructor.ConstructorError(
            None, None,
            f'expected a scalar or sequence node, but found {node.id}',
            node.start_mark
        )

    for var in vars:
        if var in os.environ:
            value = os.environ[var]
            # Resolve value to Python type using YAML's implicit resolvers
            tag = loader.resolve(yaml.nodes.ScalarNode, value, (True, False))
            return loader.construct_object(yaml.nodes.ScalarNode(tag, value))

    return default


def add_env_tag(loader: yaml.Loader) -> yaml.Loader:
    """ Modify and return Loader with env tag support. """
    loader.add_constructor('!ENV', construct_env_tag)
    return loader
