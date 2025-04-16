"""Tests for SMA Energy Meter integration."""
import unittest
from unittest.mock import Mock, patch, MagicMock
import socket
import binascii

from custom_components.sma_energy_meter.speedwiredecoder import decode_speedwire
from custom_components.sma_energy_meter.coordinator import SMAEnergyMeterCoordinator

# Sample test data packets (real SMA Energy Meter data samples)
SMA_EM_PACKET = binascii.unhexlify(
    b'534d4100000402a000000001024400106069010e7142d1eb5fc90dd0000104000000871300010800000000165'
    b'22f0068000204000000000000020800000000089d14b860000304000000000000030800000000c125c1480004'
    b'04000000115100040800000000a7050800000909040000008892000908000000008f29a800000a040000000000'
    b'000a0800000000095f5de8000d04000000039a0015040000006042001508000000003fc2d8800016040000000000'
    b'00160800000000050c92b000170400000000000017080000000004b9fc4800180400000011c1001808000000000453'
    b'f5e0001d04000000604200350400000003ae'
)

SMA_HM_PACKET = binascii.unhexlify(
    b'534d4100000402a000000001024c001060690174b2fbdb0a6133fea4000104000000000000010800000000'
    b'01d65b2ef800020400000000be8000020800000000078186456000030400000000177800030800000000'
    b'0134454f9000040400000000000000040800000000d523a75000090400000000000000090800000000020f'
    b'76bbf8000a0400000000bf8f000a0800000000078acca8e8000d04000000039e00150400000000000000150800'
    b'0000007d8bb68000290400000000000000290800000000cc8c5c9000'
)


class TestSpeedwireDecoder(unittest.TestCase):
    """Test the speedwire decoder function."""

    def test_decode_sma_em_packet(self):
        """Test decoding a SMA Energy Meter packet."""
        result = decode_speedwire(SMA_EM_PACKET)

        # Check if we have the basic expected values
        self.assertIn('serial', result)
        self.assertIn('pconsume', result)
        self.assertIn('psupply', result)

        # Check the units
        self.assertEqual(result.get('pconsumeunit'), 'W')

        # Check specific value
        if 'pconsume' in result:
            self.assertIsInstance(result['pconsume'], float)

    def test_decode_invalid_packet(self):
        """Test decoding an invalid packet."""
        result = decode_speedwire(b'INVALID_PACKET')
        self.assertEqual(result, {})

        # The decoder appears to extract a serial of 0 from this input
        result = decode_speedwire(b'SMA\x00\x00\x00')
        self.assertEqual(result, {'serial': 0})


class TestSMAEnergyMeterCoordinator(unittest.TestCase):
    """Test the SMA Energy Meter Coordinator."""

    def setUp(self):
        """Set up test environment."""
        self.hass = MagicMock()
        self.hass.async_add_executor_job = lambda func, *args, **kwargs: func(*args, **kwargs)
        # Replace direct lambda assignment with side_effect
        self.hass.add_job.side_effect = lambda func, *args, **kwargs: None

    @patch('socket.socket')
    def test_setup_socket(self, mock_socket):
        """Test socket setup."""
        # Setup mock socket
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance

        # Create coordinator
        coordinator = SMAEnergyMeterCoordinator(self.hass, "0.0.0.0")

        # Call setup socket
        coordinator._setup_socket()

        # Verify socket was created with correct parameters
        mock_socket.assert_called_once_with(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )

        # Verify socket options were set
        mock_sock_instance.setsockopt.assert_any_call(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )

        # Verify bind was called
        mock_sock_instance.bind.assert_called_once()

        # Verify timeout was set
        mock_sock_instance.settimeout.assert_called_once_with(5)

    @patch('custom_components.sma_energy_meter.coordinator.decode_speedwire')
    def test_process_data(self, mock_decode):
        """Test processing received data."""
        # Setup mock decode function
        mock_decode.return_value = {
            'serial': 123456,
            'pconsume': 100.0,
            'pconsumeunit': 'W',
        }

        # Create coordinator
        coordinator = SMAEnergyMeterCoordinator(self.hass, "0.0.0.0")

        # Process data
        coordinator._process_data(SMA_EM_PACKET)

        # Verify decode function was called with correct data
        mock_decode.assert_called_once_with(SMA_EM_PACKET)

        # Verify data was stored
        self.assertIn(123456, coordinator.meters)
        self.assertEqual(coordinator.meters[123456]['pconsume'], 100.0)

        # Verify update listeners was called
        self.hass.add_job.assert_called_once()


class TestSensorSetup(unittest.TestCase):
    """Test sensor setup and entity creation."""

    def setUp(self):
        """Set up test environment."""
        self.hass = MagicMock()
        self.entry = MagicMock()

    @patch('custom_components.sma_energy_meter.sensor._create_sensors_for_meter')
    def test_setup_entry(self, mock_create_sensors):
        """Test setting up sensors from config entry."""
        from custom_components.sma_energy_meter.sensor import async_setup_entry
        import asyncio

        # Setup mocks
        coordinator = MagicMock()
        coordinator.get_all_serials.return_value = [123456]
        self.hass.data = {'sma_energy_meter': {self.entry.entry_id: coordinator}}

        # Call setup_entry and run it as an async function
        asyncio.run(async_setup_entry(self.hass, self.entry, Mock()))

        # Check if _create_sensors_for_meter was called
        coordinator.async_add_listener.assert_called_once()

        # Simulate the callback
        callback = coordinator.async_add_listener.call_args[0][0]
        callback()

        # Verify sensors were created
        mock_create_sensors.assert_called_once_with(coordinator, 123456)


if __name__ == '__main__':
    unittest.main()