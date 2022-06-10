"""DDL Vector constants."""
from __future__ import annotations
import platform

from homeassistant.const import STATE_UNAVAILABLE


ANKI_APP_KEY = "aung2ieCho3aiph7Een3Ei"
API_URL = "https://accounts.api.anki.com/1/sessions"
TOKEN_URL = "https://session-certs.token.global.anki-services.com/vic/"
USER_AGENT = f"Vector-sdk-HomeAssistant/{platform.python_implementation()}/{platform.python_version()}"

DOMAIN = "vector_robot"
UPDATE_SIGNAL = "vector_update"

CONF_ID = "vector_id"
CONF_IP = "vector_ip"
CONF_SERIAL = "vector_serial"

PLATFORMS = ["sensor", "button"]

# Startup banner
STARTUP = """
-------------------------------------------------------------------
Digital Dream Labs Vector integration

Version: %s
This is a custom integration
If you have any issues with this you need to open an issue here:
https://github.com/mtrab/vector_robot/issues
-------------------------------------------------------------------
"""

# Service constants
SERVICE_GOTO_CHARGER = "goto_charger"
SERVICE_LEAVE_CHARGER = "leave_charger"
SERVICE_SPEAK = "speak"

# Attribs
ATTR_MESSAGE = "message"
ATTR_USE_VECTOR_VOICE = "vector_voice"

# Battery states
STATE_LOW = "low"
STATE_NORMAL = "normal"
STATE_FULL = "full"

# Update signals
UPDATE_BATTERY = "update_battery"

# Battery map
BATTERYMAP_TO_STATE = {
    0: STATE_UNAVAILABLE,
    1: STATE_LOW,
    2: STATE_NORMAL,
    3: STATE_FULL,
}
