"""DDL Vector constants."""
from __future__ import annotations

DOMAIN = "vector_robot"

CONF_ID = "vector_id"
CONF_IP = "vector_ip"
CONF_SERIAL = "vector_serial"

PLATFORMS = ["sensor"]

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
