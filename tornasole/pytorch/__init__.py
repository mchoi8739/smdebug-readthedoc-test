from .hook import TornasoleHook
from .torch_collection import Collection, CollectionManager

from .torch_collection import get_collections, get_collection, \
  load_collections,  \
  add_to_collection, add_to_default_collection, reset_collections
from tornasole import SaveConfig, ReductionConfig
from tornasole import modes