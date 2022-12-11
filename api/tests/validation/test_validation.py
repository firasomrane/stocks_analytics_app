# flake8
import unittest
from enum import Enum

from validation.validation import (
    ComparisonValidation,
    TwoElementsComparisonValidation,
    ValueBelongsToFieldValidation,
    convert_to_set,
)

TC = unittest.TestCase()


def test_comparison_validation():

    assert ComparisonValidation(
        field_name='any',
        field_value=10,
        max_value=20,
    ).is_valid

    assert (
        ComparisonValidation(
            field_name='any',
            field_value=30,
            max_value=20,
        ).is_valid
        is False
    )

    with TC.assertRaises(ValueError):
        ComparisonValidation(field_name='any', field_value=10)

    with TC.assertRaises(ValueError):
        ComparisonValidation(field_name='any', field_value='a', max_value='a', min_value='b')

    # Test error messages:
    assert (
        ComparisonValidation(
            field_name='any',
            field_value=10,
            max_value=20,
        ).error_message
        == 'any should be less than 20'  # noqa
    )


def test_two_elements_comparison_validation():
    assert TwoElementsComparisonValidation(
        should_be_smaller_name='small',
        should_be_smaller_value='1',
        should_be_bigger_name='big',
        should_be_bigger_value='2',
    ).is_valid

    assert (
        TwoElementsComparisonValidation(
            should_be_smaller_name='small',
            should_be_smaller_value='2',
            should_be_bigger_name='big',
            should_be_bigger_value='1',
        ).is_valid
        is False  # noqa
    )


class TestEnum(Enum):
    VALUE1 = 'value1'
    VALUE2 = 'value2'


def test_convert_to_set():

    TC.assertSetEqual(convert_to_set(TestEnum), {'value1', 'value2'})
    TC.assertSetEqual(convert_to_set([1, 2]), {1, 2})


def test_value_belongs_to_field_validation():

    assert ValueBelongsToFieldValidation(field_name='any', field_value='value1', valid_values=TestEnum).is_valid

    assert (
        ValueBelongsToFieldValidation(field_name='any', field_value='non_existing', valid_values=TestEnum).is_valid
        is False
    )  # noqa
    assert (
        ValueBelongsToFieldValidation(field_name='any', field_value=0, valid_values={1, 2, 3}).is_valid is False
    )  # noqa

    assert ValueBelongsToFieldValidation(field_name='any', field_value=3, valid_values=[1, 2, 3]).is_valid
