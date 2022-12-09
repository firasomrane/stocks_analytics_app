from abc import ABC, abstractmethod

from fastapi import HTTPException


class Validation(ABC):
    """
    Base interface to implement validation
    """

    def __init__(self) -> None:
        pass

    @property
    @abstractmethod
    def is_valid(self) -> bool:
        """
        Returns if the inputs are valid
        """
        pass

    @property
    @abstractmethod
    def error_message(self) -> str:
        """
        Implement custom error message to be passed when the input is not valid
        """
        pass

    @property
    def http_exception(self) -> HTTPException:
        """
        http exception to return when input is not valid
        """
        return HTTPException(status_code=422, detail=self.error_message)
