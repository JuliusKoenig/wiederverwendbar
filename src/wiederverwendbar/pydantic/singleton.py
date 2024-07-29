import logging

from pydantic._internal._model_construction import ModelMetaclass

from wiederverwendbar.singleton import Singleton

logger = logging.getLogger(__name__)


class ModelSingleton(ModelMetaclass, Singleton):
    """
    Singleton metaclass
    """

    ...
