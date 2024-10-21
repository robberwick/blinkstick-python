from .main import main
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("blinkstick")
except PackageNotFoundError:
    __version__ = "BlinkStick package not installed"