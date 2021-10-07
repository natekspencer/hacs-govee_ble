"""Constants for the Govee BLE HCI monitor sensor integration."""
DOMAIN = "govee_ble"
SCANNER = "scanner"

DATA_UNSUBSCRIBE = "unsubs"
EVENT_DEVICE_ADDED_TO_REGISTRY = f"{DOMAIN}_device_added_to_registry"

CONF_EXCLUDE_DEVICES = "exclude_devices"
CONF_KEEP_ALIVE = "keep_alive"
CONF_LOG_ADVERTISEMENTS = "log_advertisements"
CONF_LOG_NOTIFICATIONS = "log_notifications"
DEFAULT_EXCLUDE_DEVICES = ""
DEFAULT_KEEP_ALIVE = False
DEFAULT_LOG_ADVERTISEMENTS = False
DEFAULT_LOG_NOTIFICATIONS = False
