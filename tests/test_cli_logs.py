import pytest
import argparse
from src.cli.main import non_negative_int


class TestCLILogsValidation:
    def test_valid_positive_values(self):
        assert non_negative_int("1") == 1
        assert non_negative_int("50") == 50
        assert non_negative_int("1000") == 1000

    def test_zero_value(self):
        assert non_negative_int("0") == 0

    def test_negative_values_raise_error(self):
        with pytest.raises(argparse.ArgumentTypeError, match="must be a non-negative integer"):
            non_negative_int("-1")

        with pytest.raises(argparse.ArgumentTypeError, match="must be a non-negative integer"):
            non_negative_int("-999")

    def test_non_integer_values_raise_error(self):
        with pytest.raises(argparse.ArgumentTypeError, match="is not a valid integer"):
            non_negative_int("abc")

        with pytest.raises(argparse.ArgumentTypeError, match="is not a valid integer"):
            non_negative_int("5.5")

        with pytest.raises(argparse.ArgumentTypeError, match="is not a valid integer"):
            non_negative_int("")


class TestCLIParserIntegration:
    def test_parser_with_valid_tail(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--tail", "-t", type=non_negative_int, default=50)
        
        args = parser.parse_args(["--tail", "25"])
        assert args.tail == 25

        args_default = parser.parse_args([])
        assert args_default.tail == 50

        args_zero = parser.parse_args(["--tail", "0"])
        assert args_zero.tail == 0

    def test_parser_with_invalid_tail(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--tail", "-t", type=non_negative_int, default=50)

        # argparse.parse_args prints to stderr and calls sys.exit(2) when type validation fails
        # We can test by catching SystemExit
        with pytest.raises(SystemExit):
            parser.parse_args(["--tail", "-10"])

        with pytest.raises(SystemExit):
            parser.parse_args(["--tail", "invalid"])
