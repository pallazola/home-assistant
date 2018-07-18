"""
Support for Switchmate.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.switchmate/
"""
import logging
from datetime import timedelta

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.switch import SwitchDevice, PLATFORM_SCHEMA
from homeassistant.const import CONF_FRIENDLY_NAME, CONF_MAC
from homeassistant.exceptions import PlatformNotReady
from homeassistant.util import Throttle

REQUIREMENTS = ['bluepy==1.1.4']

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Switchmate'
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MAC): cv.string,
    vol.Optional(CONF_FRIENDLY_NAME, default=DEFAULT_NAME): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None) -> None:
    """Perform the setup for Xiaomi devices."""
    friendly_name = config.get(CONF_FRIENDLY_NAME)
    mac_addr = config.get(CONF_MAC)
    add_devices([Switchmate(mac_addr, friendly_name)], True)


class Switchmate(SwitchDevice):
    """Representation of a Switchmate."""

    def __init__(self, mac, friendly_name) -> None:
        """Initialize the Switchmate."""
        # pylint: disable=import-error
        import bluepy
        self._state = False
        self._friendly_name = friendly_name
        self._handle = 0x2e
        self._mac = mac
        try:
            self._device = bluepy.btle.Peripheral(self._mac,
                                                  bluepy.btle.ADDR_TYPE_RANDOM)
        except bluepy.btle.BTLEException:
            _LOGGER.error("Failed to setup switchmate", exc_info=True)
            raise PlatformNotReady()

    @property
    def unique_id(self) -> str:
        """Return a unique, HASS-friendly identifier for this entity."""
        return '{0}_{1}'.format(self._mac.replace(':', ''), self.entity_id)

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._friendly_name

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self) -> None:
        """Synchronize state with switch."""
        self._state = self._device.readCharacteristic(self._handle) == b'\x00'

    @property
    def is_on(self) -> bool:
        """Return true if it is on."""
        return self._state

    def turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        self._device.writeCharacteristic(self._handle, b'\x00', True)
        self._state = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        self._device.writeCharacteristic(self._handle, b'\x01', True)
        self._state = False
        self.schedule_update_ha_state()