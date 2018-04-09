"""Tests the gps module."""
import unittest
from mock import patch
import pynmea2
import pytest
import control.gps

# mock gps nmea 0183 messages
NMEA_MSG_GGA = "$GNGGA,183236.00,3311.64266,N,08730.77826,W,1,07,1.24,85.4,M,-29.8,M,,*4A"
NMEA_MSG_GGA2 = "$GNGGA,183235.00,3311.64268,N,08730.77830,W,1,07,1.24,85.5,M,-29.8,M,,*41"
NMEA_MSG_RMC = "$GNRMC,183235.00,A,3311.64268,N,08730.77830,W,0.169,,040318,,,A*7B"
NMEA_MSG_GSV = "$GPGSV,2,2,06,26,61,047,42,31,27,063,38*70"
NMEA_MSG_NOLOCK = "$GNGGA,,,,,,0,00,99.99,,,,,,*56"
NMEA_MSG_CORRUPT = "..,,,,99,,,,"


def expected_gps_reading(msg):
    """Helper function returns expected parsed nmea message as a GpsReading"""
    parsed_msg = pynmea2.parse(msg)
    return control.gps.GpsReading(parsed_msg.latitude,
                                  parsed_msg.longitude,
                                  parsed_msg.altitude,
                                  parsed_msg.timestamp)


class GPStest(unittest.TestCase):
    """GPS module unit tests."""
    def setUp(self):
        self.patcher = patch('serial.Serial')
        self.addCleanup(self.patcher.stop)
        self.mock_serial_class = self.patcher.start()
        self.mock_serial_connect = self.mock_serial_class.return_value
        self.gps = control.gps.Gps("connection", 9600)

    def test_gps_gga_msg_read(self):
        """Test reading a proper GGA message."""
        self.mock_serial_connect.readline.return_value = NMEA_MSG_GGA
        expected_reading = expected_gps_reading(NMEA_MSG_GGA)
        actual_reading = self.gps.read()
        self.assertEqual(actual_reading, expected_reading)

    def test_gps_multiple_msg_types(self):
        """Test reading multiple nmea message types."""
        msg_return_list = [NMEA_MSG_RMC, NMEA_MSG_GSV, NMEA_MSG_GGA2]
        self.mock_serial_connect.readline.side_effect = msg_return_list
        expected_reading = expected_gps_reading(NMEA_MSG_GGA2)
        actual_reading = self.gps.read()
        self.assertEqual(actual_reading, expected_reading)

    def test_gps_satellite_no_lock_msg(self):
        """Test reading a nmea message with no satellite lock."""
        msg_return_list = [NMEA_MSG_RMC, NMEA_MSG_NOLOCK, NMEA_MSG_GGA]
        self.mock_serial_connect.readline.side_effect = msg_return_list
        expected_reading = expected_gps_reading(NMEA_MSG_NOLOCK)
        actual_reading = self.gps.read()
        self.assertEqual(actual_reading, expected_reading)

    def test_gps_corrupt_msg(self):
        """Test reading a corrupt nmea message."""
        msg_return_list = [NMEA_MSG_CORRUPT, NMEA_MSG_CORRUPT, NMEA_MSG_CORRUPT, NMEA_MSG_GGA]
        self.mock_serial_connect.readline.side_effect = msg_return_list
        expected_reading = expected_gps_reading(NMEA_MSG_GGA)
        actual_reading = self.gps.read()
        self.assertEqual(actual_reading, expected_reading)

    def test_gps_corrupt_msg2(self):
        """Test reading a corrupt nmea message mixed with other valid messages."""
        msg_return_list = [NMEA_MSG_CORRUPT, NMEA_MSG_GSV,
                           NMEA_MSG_RMC, NMEA_MSG_GGA, NMEA_MSG_CORRUPT]
        self.mock_serial_connect.readline.side_effect = msg_return_list
        expected_reading = expected_gps_reading(NMEA_MSG_GGA)
        actual_reading = self.gps.read()
        self.assertEqual(actual_reading, expected_reading)

    def test_gps_corrupt_msg3(self):
        """Test reading max number of corrupt nmea messages."""
        with pytest.raises(control.gps.GpsReadError):
            msg_return_list = [NMEA_MSG_CORRUPT, NMEA_MSG_CORRUPT,
                               NMEA_MSG_CORRUPT, NMEA_MSG_CORRUPT, NMEA_MSG_GGA]
            self.mock_serial_connect.readline.side_effect = msg_return_list
            self.gps.read()


def test_offset_and_locations_are_inverse_functions():
    """Tests that get_location_offset and get_relative_from_location are
    inverse functions.
    """
    origin = control.gps.GpsReading(33.142220, -87.582491, 0, 0)
    offset = control.gps.get_location_offset(origin, 10, 15)
    tup = control.gps.get_relative_from_location(origin, offset)
    assert tup[0] - 15 < 1
    assert tup[1] - 10 < 1

    offset = control.gps.get_location_offset(origin, -7, -15)
    tup = control.gps.get_relative_from_location(origin, offset)
    assert tup[0] + 15 < 1
    assert tup[1] + 7 < 1
