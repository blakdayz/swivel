import logging


class LocationSubscriber:
    """
    LocationSubscriber is a class that subscribes to location updates and performs actions when the location is updated.

    Methods:
    --------
        __init__(event_bus)
            Initializes the LocationSubscriber with an event bus and subscribes to location updates.

        on_location_updated(location_data)
            Callback method that is called when the location is updated. It logs the updated location data.
    """

    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.event_bus.subscribe_location_updated(self.on_location_updated)

    def on_location_updated(self, location_data):
        # Perform actions when location is updated, e.g., log or send the data
        latitude, longitude = location_data
        logging.info(
            f"Location updated (Subscriber): Latitude = {latitude}, Longitude = {longitude}"
        )



class WifiSubscriber:
    """
    Class representing a WiFi subscriber that listens for updates on WiFi networks.

    Methods
    -------
    __init__(self, event_bus)
        Subscribes to WiFi network updates.

    on_wifi_networks_updated(self, wifi_networks_data)
        Logs the updated list of WiFi networks.
    """

    def __init__(self, event_bus):
        event_bus.subscribe_wifi_networks_updated(
            self.on_wifi_networks_updated
        )

    def on_wifi_networks_updated(self, wifi_networks_data):
        logging.info("WiFi networks updated:")
        for network in wifi_networks_data:
            logging.info(network)
