"""Data coordinator for SMA Energy Meter."""
import asyncio
import logging
import socket
import struct
import threading
from datetime import timedelta
from typing import Dict, List, Optional

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .speedwiredecoder import decode_speedwire

_LOGGER = logging.getLogger(__name__)

MCAST_GRP = '239.12.255.254'
MCAST_PORT = 9522

class SMAEnergyMeterCoordinator(DataUpdateCoordinator):
    """Class to manage fetching SMA Energy Meter data."""

    def __init__(self, hass: HomeAssistant, host: str):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="SMA Energy Meter",
            update_interval=timedelta(seconds=30),  # Fallback update interval
        )
        self.host = host
        self.meters = {}  # Dictionary to store meter data by serial number
        self._socket = None
        self._thread = None
        self._thread_running = False

    async def async_start(self):
        """Start the data collection thread."""
        await self.hass.async_add_executor_job(self._setup_socket)
        self._thread_running = True
        self._thread = threading.Thread(target=self._listen_thread, daemon=True)
        self._thread.start()

    async def async_stop(self):
        """Stop the data collection thread."""
        self._thread_running = False
        if self._socket:
            await self.hass.async_add_executor_job(self._socket.close)
            self._socket = None
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None

    def _setup_socket(self):
        """Set up the multicast socket."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', MCAST_PORT))
            mreq = struct.pack("4s4s", socket.inet_aton(MCAST_GRP), socket.inet_aton(self.host))
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            sock.settimeout(5)  # Set timeout so the thread can be stopped
            self._socket = sock
            _LOGGER.debug("Successfully set up multicast socket on %s", self.host)
        except Exception as err:
            _LOGGER.error("Error setting up multicast socket: %s", err)
            self._socket = None

    def _listen_thread(self):
        """Listen for SMA Energy Meter broadcasts."""
        while self._thread_running and self._socket:
            try:
                data = self._socket.recv(1024)
                self._process_data(data)
            except socket.timeout:
                continue
            except Exception as err:
                if self._thread_running:
                    _LOGGER.error("Error in SMA Energy Meter listener thread: %s", err)

    def _process_data(self, data):
        """Process received data and update state."""
        try:
            emparts = decode_speedwire(data)
            if not emparts:
                return

            serial = emparts.get('serial')
            if not serial:
                return

            # Store new data for this meter
            self.meters[serial] = emparts

            # Trigger callback to notify sensors of new data
            self.hass.add_job(self.async_update_listeners)

            _LOGGER.debug("Received update from SMA Energy Meter %s", serial)
        except Exception as err:
            _LOGGER.error("Error processing SMA Energy Meter data: %s", err)

    async def _async_update_data(self):
        """Return all meter data."""
        # This is only used for the fallback update mechanism
        # Data is primarily updated through the listener thread
        return self.meters

    def get_meter_data(self, serial):
        """Get data for a specific meter."""
        return self.meters.get(serial)

    def get_all_serials(self):
        """Get all detected meter serials."""
        return list(self.meters.keys())