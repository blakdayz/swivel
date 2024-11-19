class EventBus:
    """Simple event bus for broadcasting messages to subscribers."""

    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_type, callback):
        """Subscribe to an event type with a callback function that accepts data."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def unsubscribe(self, event_type, callback):
        """Unsubscribe from an event type."""
        if event_type in self.subscribers:
            self.subscribers[event_type].remove(callback)

    def publish(self, event_type, data):
        """Broadcast an event to all subscribers of the given event type."""
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                callback(data)

    def publish_device_found(self, data):
        """
        Publish a device found event.
        :param data:
        :return:
        """
        self.publish("device_found", data)

    def publish_device_lost(self, data):
        """
        Publish a device lost event.
        :param data:
        :return:
        """
        self.publish("device_lost", data)

    def publish_device_appeared(self, data):
        """
        1       Publish a device appeared event.
                :param data:
                :return:
        """
        self.publish("device_appeared", data)

    def subscribe_device_updated(self, callback):
        """Subscribe to device updated events."""
        self.subscribe("device_updated", callback)

    def subscribe_device_created(self, callback):
        """Subscribe to device created events"""
        self.subscribe("device_created", callback)

    def subscribe_device_deleted(self, callback):
        """
        subscribe to device deleted events
        :param callback:
        :return:
        """
        self.subscribe("device_deleted", callback)

    def subscribe_device_relocated(self, callback):
        """
        subscribe to device relocated events
        :param callback:
        :return:
        """
        self.subscribe("device_relocated", callback)

    def subscribe_location_updated(self, callback):
        """Subscribe to location updated events."""
        self.subscribe("location_updated", callback)

    def publish_location_updated(self, data):
        """Publish a location updated event."""
        self.publish("location_updated", data)

    def subscribe_wifi_networks_updated(self, callback):
        """Subscribe to WiFi networks updated events."""
        self.subscribe("wifi_networks_updated", callback)

    def publish_wifi_networks_updated(self, data):
        """Publish a WiFi networks updated event."""
        self.publish("wifi_networks_updated", data)


if __name__ == "__main__":
    event_bus = EventBus()
    # example
