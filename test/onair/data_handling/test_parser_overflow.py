"""Out-of-range telemetry must follow the existing missing-value policy."""

import math
import sys

import pytest

from onair.data_handling import parser_util


@pytest.mark.parametrize("remove_str", [False, True])
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(sign * 10**exponent, id=f"sign{sign}-exp{exponent}")
        for exponent in (309, 1000, 5000)
        for sign in (1, -1)
    ],
)
def test_overflow_preserves_neighboring_measurements(monkeypatch, value, remove_str):
    warnings = []
    monkeypatch.setattr(parser_util, "print_msg", lambda *args: warnings.append(args))
    source = [1, value, -2]
    result = parser_util.floatify_input(source, remove_str=remove_str)
    assert source == [1, value, -2]
    if remove_str:
        assert result == [1.0, -2.0]
        assert warnings == []
    else:
        assert len(result) == 3
        assert result[0] == 1.0 and result[2] == -2.0
        assert math.isnan(result[1])
        assert len(warnings) == 1
        assert "substituting math.nan" in warnings[0][0]
        assert warnings[0][1] == ["WARNING"]


@pytest.mark.parametrize("container", [int, list, dict], ids=["int", "list", "dict"])
def test_warning_survives_integer_repr_limit(monkeypatch, container):
    if not hasattr(sys, "set_int_max_str_digits"):
        pytest.skip("interpreter has no integer string conversion limit")
    huge = 1 << 5000
    value = huge if container is int else [huge] if container is list else {"x": huge}
    warnings = []
    monkeypatch.setattr(parser_util, "print_msg", lambda *args: warnings.append(args))
    previous_limit = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(640)
        result = parser_util.floatify_input([value, 7])
    finally:
        sys.set_int_max_str_digits(previous_limit)
    assert len(result) == 2 and math.isnan(result[0]) and result[1] == 7.0
    assert warnings == [
        (
            f"floatify_input: could not parse <{container.__name__}> to a finite float; "
            "substituting math.nan",
            ["WARNING"],
        )
    ]


def test_representable_large_numbers_and_existing_warning_are_unchanged(monkeypatch):
    warnings = []
    monkeypatch.setattr(parser_util, "print_msg", lambda *args: warnings.append(args))
    assert parser_util.floatify_input([10**308, -(10**308), 0]) == [1e308, -1e308, 0.0]
    assert warnings == []
    result = parser_util.floatify_input(["-", "3.5"])
    assert math.isnan(result[0]) and result[1] == 3.5
    assert warnings == [
        (
            "floatify_input: could not parse '-' to a finite float; substituting math.nan",
            ["WARNING"],
        )
    ]
