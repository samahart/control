"""Tests the communication module."""
import json
from mock import patch, call
import control.communication


@patch('serial.Serial')
def test_receiving_valid_data(mock_serial_class):
    """Confirm the json data is returned as actual data."""
    expected = {'test': 5}  # Random data
    serial_mock = mock_serial_class.return_value
    serial_mock.readline.return_value = json.dumps(expected)
    comm = control.communication.Communication('port', 2)
    actual = comm.receive()
    assert actual == expected


@patch('serial.Serial')
def test_receiving_no_data(mock_serial_class):
    """Confirm the receive returns a None when timeout is called."""
    expected = None  # No Data
    serial_mock = mock_serial_class.return_value
    serial_mock.readline.return_value = None
    comm = control.communication.Communication('port', 2)
    actual = comm.receive()
    assert actual == expected


@patch('serial.Serial')
def test_receiving_bad_data(mock_serial_class):
    """Confirm that None is returned when json data is corrupt."""
    corrupt = '{"some_key": 777'
    expected = None
    serial_mock = mock_serial_class.return_value
    serial_mock.readline.return_value = corrupt
    comm = control.communication.Communication('port', 2)
    actual = comm.receive()
    assert actual == expected


@patch('serial.Serial')
def test_sending_valid_data(mock_serial_class):
    """Confirm the jsonned data is passed to pyserial correctly."""
    serial_mock = mock_serial_class.return_value
    data = {'test': 5}  # Random data
    expected_calls = [call(json.dumps(data)), call(b'\n')]
    comm = control.communication.Communication('port', 2)
    comm.send(data)
    serial_mock.write.assert_has_calls(expected_calls)
