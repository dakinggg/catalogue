# coding: utf8
from __future__ import unicode_literals

from collections import OrderedDict
import sys

try:  # Python 3.8
    import importlib.metadata as importlib_metadata
except ImportError:
    import importlib_metadata

if sys.version_info[0] == 2:
    basestring_ = basestring  # noqa: F821
else:
    basestring_ = str

# Ony ever call this once for performance reasons
AVAILABLE_ENTRY_POINTS = importlib_metadata.entry_points()

# This is where functions will be registered
REGISTRY = OrderedDict()


def create(*namespace, entry_points=False):
    """Create a new registry.

    *namespace (str): The namespace, e.g. "spacy" or "spacy", "architectures".
    RETURNS (Tuple[Callable]): The setter (decorator to register functions)
        and getter (to retrieve functions).
    """
    if check_exists(*namespace):
        raise RegistryError("Namespace already exists: {}".format(namespace))
    return Registry(namespace, entry_points=entry_points)


class Registry(object):
    def __init__(self, namespace, entry_points=False):
        """Initialize a new registry.

        namespace (Tuple[str]): The namespace.
        entry_points (bool): Whether to also check for entry points.
        RETURNS (Registry): The newly created object.
        """
        self.namespace = namespace
        self.entry_point_namespace = "_".join(namespace)
        if entry_points:
            for name, value in self.get_entry_points().items():
                self.register(name, func=value)

    def register(self, name, **kwargs):
        """Register a function for a given namespace.

        name (str): The name to register under the namespace.
        func (Any): Optional function to register (if not used as decorator).
        RETURNS (Callable): The decorator.
        """

        def do_registration(func):
            _set(list(self.namespace) + [name], func)
            return func

        func = kwargs.get("func")
        if func is not None:
            return do_registration(func)
        return do_registration

    def get(self, name):
        """Get the registered function for a given name.

        name (str): The name.
        RETURNS (Any): The registered function.
        """
        namespace = list(self.namespace) + [name]
        if not check_exists(*namespace):
            err = "Cant't find '{}' in registry {}"
            raise RegistryError(err.format(name, " -> ".join(self.namespace)))
        return _get(namespace)

    def get_all(self):
        """Get a all functions for a given namespace.

        namespace (Tuple[str]): The namespace to get.
        RETURNS (Dict[str, Any]): The functions, keyed by name.
        """
        global REGISTRY
        result = OrderedDict()
        for keys, value in REGISTRY.items():
            if len(self.namespace) == len(keys) - 1 and all(
                self.namespace[i] == keys[i] for i in range(len(self.namespace))
            ):
                result[keys[-1]] = value
        return result

    def get_entry_points(self):
        """Get registered entry points from other packages for this namespace.

        RETURNS (dict): Entry points, keyed by name.
        """
        result = {}
        for entry_point in AVAILABLE_ENTRY_POINTS.get(self.entry_point_namespace, []):
            result[entry_point.name] = entry_point.load()
        return result

    def get_entry_point(self, name, default=None):
        """Check if registered entry point is available for a given name in the
        namespace and load it. Otherwise, return None.

        name (unicode): Name of entry point to load.
        RETURNS: The loaded entry point or None.
        """
        for entry_point in AVAILABLE_ENTRY_POINTS.get(self.entry_point_namespace, []):
            if entry_point.name == name:
                return entry_point.load()
        return default


def check_exists(*namespace):
    """Check if a namespace exists.

    *namespace (str): The namespace.
    RETURNS (bool): Whether the namespace exists.
    """
    return namespace in REGISTRY


def _get(namespace):
    """Get the value for a given namespace.

    namespace (Tuple[str]): The namespace.
    RETURNS: The value for the namespace.
    """
    global REGISTRY
    if not all(isinstance(name, basestring_) for name in namespace):
        err = "Invalid namespace. Expected tuple of strings, but got: {}"
        raise ValueError(err.format(namespace))
    namespace = tuple(namespace)
    if namespace not in REGISTRY:
        err = "Can't get namespace {} (not in registry)".format(namespace)
        raise RegistryError(err)
    return REGISTRY[namespace]


def _get_all(namespace):
    """Get all matches for a given namespace, e.g. ("a", "b", "c") and
    ("a", "b") for namespace ("a", "b").

    namespace (Tuple[str]): The namespace.
    RETURNS (Dict[Tuple[str], Any]): All entries for the namespace, keyed
        by their full namespaces.
    """
    global REGISTRY
    result = OrderedDict()
    for keys, value in REGISTRY.items():
        if len(namespace) <= len(keys) and all(
            namespace[i] == keys[i] for i in range(len(namespace))
        ):
            result[keys] = value
    return result


def _set(namespace, func):
    """Set a value for a given namespace.

    namespace (Tuple[str]): The namespace.
    func (Callable): The value to set.
    """
    global REGISTRY
    REGISTRY[tuple(namespace)] = func


def _remove(namespace):
    """Remove a value for a given namespace.

    namespace (Tuple[str]): The namespace.
    RETURNS: The removed value.
    """
    global REGISTRY
    namespace = tuple(namespace)
    if namespace not in REGISTRY:
        err = "Can't get namespace {} (not in registry)".format(namespace)
        raise RegistryError(err)
    removed = REGISTRY[namespace]
    del REGISTRY[namespace]
    return removed


class RegistryError(ValueError):
    pass
