# This import is used by mkdocs plugin entry point
from .plugin import ProtobufPlugin  # noqa: F401
from .file_cache import ProtoFileCache  # noqa: F401
from .i18n_support import I18nSupport  # noqa: F401

__version__ = '0.1.1-dev0'  # Will be updated by bumpversion
