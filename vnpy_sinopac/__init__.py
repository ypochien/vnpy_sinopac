try:
    from .gateway import SinopacGateway
except ImportError:
    pass

import importlib_metadata

try:
    __version__ = importlib_metadata.version("vnpy_sinopac")
except importlib_metadata.PackageNotFoundError:
    __version__ = "dev"
