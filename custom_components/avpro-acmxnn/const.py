"""Constants for the AVPro matrix switch integration."""
from typing import Final

# This is the internal name of the integration, it should also match the directory
# name for the integration.
DOMAIN: Final           = "avpro-acmxnn"
MANUFACTURER: Final     = "AVPro Edge"

WS_STATE_CONNECTED: Final      = "connected"
WS_STATE_DISCONNECTED: Final   = "disconnected"
WS_STATE_STARTING: Final       = "starting"
WS_STATE_STOPPED: Final        = "stopped"
WS_MAX_FAILED_ATTEMPTS: Final  = 5

OUTPUT_TYPE_VIDEO: Final       = "V"
OUTPUT_TYPE_AUDIO: Final       = "A"