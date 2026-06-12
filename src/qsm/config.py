from importlib import import_module
from pathlib import Path
from typing import Annotated, Any, Dict, Optional, Type

from pydantic import BaseModel, BeforeValidator, ConfigDict, field_validator, model_validator, ValidationInfo

from .states import State


def load_model_path(path: Optional[str]) -> Optional[Type]:
    if path is None:
        return None
    if not isinstance(path, str):
        raise TypeError("Expected dotted import path string")
    module_name, class_name = path.rsplit(".", 1)
    module = import_module(module_name)
    return getattr(module, class_name)


class QSMModuleConfig[T](BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    model: Annotated[Type[T], BeforeValidator(load_model_path)]
    kwargs: Dict[str, Any] = {}

    @field_validator("kwargs")
    @classmethod
    def inject_external_vars(cls, value: dict[str, Any], info: ValidationInfo):
        context = info.context or {}
        shared = context.get("shared", {})

        return {
            k: shared[v[1:]] if isinstance(v, str) and v.startswith("$") else v
            for k, v in value.items()
        }

    @model_validator(mode="after")
    def cast_to_class(self) -> T:
        return self.model(**self.kwargs)


class QSMConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    initial_state: str = "initial_state"
    initial_context: QSMModuleConfig[Any] = None
    max_queue_size: Optional[int] = None
    states: Dict[str, QSMModuleConfig[State]] = {}
