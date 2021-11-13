import pytest


@pytest.mark.parametrize('test_default', [
    ('test', 'expected')
])
# @pytest.mark.skip(reason='default example')
def test_default(test_input, expected):
    assert test_input is not expected
