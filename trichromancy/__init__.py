from krita import *
from .trichromancy import TrichromancyDocker

DOCKER_ID = "Trichromancy"
Application.addDockWidgetFactory(
    DockWidgetFactory(
        DOCKER_ID,
        DockWidgetFactoryBase.DockRight,
        TrichromancyDocker))
