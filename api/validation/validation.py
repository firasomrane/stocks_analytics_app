from abc import ABC, abstractmethod

from fastapi import HTTPException


class Validation(ABC):
    def __init__(self) -> None:
        pass

    @property
    @abstractmethod
    def is_valid(self) -> bool:
        pass

    @property
    @abstractmethod
    def error_message(self) -> str:
        pass

    @property
    def http_exception(self) -> HTTPException:
        return HTTPException(status_code=422, detail=self.error_message)
