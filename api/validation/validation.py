from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Iterator, Set, Type, Union

from fastapi import HTTPException


class FieldValidation(ABC):
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


class ComparisonValidation(FieldValidation):
    """ """

    def __init__(self, field_name: str, field_value: Any, max_value: Any = None, min_value: Any = None) -> None:
        super().__init__()
        # TODO add type check of value and min and max values
        if max_value is None and min_value is None:
            raise ValueError('At least one of max_value and min_value should be indicated')
        if max_value and min_value and max_value < min_value:
            raise ValueError(f'Validation max_value {max_value} should be bigger than min_value {min_value}')

        self.field_name = field_name
        self.field_value = field_value
        self.max_value = max_value
        self.min_value = min_value

    @property
    def is_valid(self) -> bool:
        # TODO add inclusive and exclusive support
        """
        Checks if field is inlusevely in the [max_value, min_value] interval
        """
        if self.max_value:
            if self.field_value > self.max_value:
                return False

        if self.min_value:
            if self.field_value < self.min_value:
                return False

        return True

    @property
    def error_message(self) -> str:
        if self.min_value and self.max_value:
            return f'{self.field_name} should be between {self.min_value} and {self.max_value}'

        elif self.min_value:
            return f'{self.field_name} should be bigger than {self.min_value}'

        elif self.max_value:
            return f'{self.field_name} should be less than {self.max_value}'


class TwoElementsComparisonValidation(FieldValidation):
    def __init__(
        self,
        should_be_smaller_name: str,
        should_be_smaller_value: Any,
        should_be_bigger_name: str,
        should_be_bigger_value: Any,
    ) -> None:
        super().__init__()
        self.should_be_smaller_name = should_be_smaller_name
        self.should_be_smaller = should_be_smaller_value
        self.should_be_bigger_name = should_be_bigger_name
        self.should_be_bigger = should_be_bigger_value

    @property
    def is_valid(self) -> bool:
        # TODO add inclusive and exclusive support
        """
        Checks if field is inlusevely in the [max_value, min_value] interval
        """
        return self.should_be_smaller <= self.should_be_bigger

    @property
    def error_message(self) -> str:
        return f'{self.should_be_bigger_name} should be bigger than {self.should_be_smaller_name}'


def convert_to_set(to_transform: Union[Type[Enum], Iterator[Any]]) -> Set[Any]:
    """
    Cast to_transform to set of str
    """
    if isinstance(to_transform, type) and issubclass(to_transform, Enum):
        return {e.value for e in to_transform}

    return set(to_transform)


class ValueBelongsToFieldValidation(FieldValidation):
    def __init__(self, field_name: str, field_value: Any, valid_values: Union[Enum, Iterator[Any]]) -> None:
        super().__init__()
        self.field_name = field_name
        self.field_value = field_value
        self.valid_values = convert_to_set(valid_values)

    @property
    def is_valid(self) -> bool:
        # TODO add inclusive and exclusive support
        """
        Checks if string is one of the valid values
        """
        return self.field_value in self.valid_values

    @property
    def error_message(self) -> str:
        return f'{self.field_name} {self.field_value} is not supported, should be equal to one of {self.valid_values}'
