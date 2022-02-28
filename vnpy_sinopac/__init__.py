import importlib_metadata
from .gateway import SinopacGateway

try:
    __version__ = importlib_metadata.version("vnpy_sinopac")
except importlib_metadata.PackageNotFoundError:
    __version__ = "dev"
