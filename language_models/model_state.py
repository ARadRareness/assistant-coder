from threading import Lock
from typing import Optional
from language_models.api.base import ApiModel
from language_models.model_manager import ModelManager


class ModelState:
    _instance = None
    _lock = Lock()

    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager

    @classmethod
    def initialize(cls, model_manager: ModelManager):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(model_manager)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            raise ValueError("ModelState is not initialized.")
        return cls._instance

    @classmethod
    def get_lock(cls):
        return cls._lock

    @classmethod
    def get_active_model(cls) -> Optional[ApiModel]:
        if cls._instance:
            return cls._instance.model_manager.active_models[0]
        return None

    @classmethod
    def get_model_manager(cls) -> Optional[ModelManager]:
        if cls._instance:
            return cls._instance.model_manager
        return None
