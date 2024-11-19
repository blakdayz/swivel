import time
import asyncio
import objc
import logging
from CoreLocation import (
    CLLocationManager,
    CLLocationCoordinate2D,
    kCLAuthorizationStatusAuthorizedAlways,
    kCLAuthorizationStatusDenied,
    kCLAuthorizationStatusRestricted,
    kCLAuthorizationStatusNotDetermined,
)
from Foundation import NSObject, NSRunLoop, NSDefaultRunLoopMode, NSDate

from swivel.events.event_subsystem import EventBus
from swivel.services.place_service import PlaceService
from swivel.services.device_service import DeviceService

# Set up logging configuration
logging.basicConfig(
    filename="swivel-location.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# Delegate to handle location updates
class LocationManagerDelegate(NSObject):
    """
    LocationManagerDelegate is an NSObject subclass that acts as a delegate for handling location and heading updates.

    Methods
    -------
    - init():
        Initializes the LocationManagerDelegate instance.
    - locationManager_didUpdateLocations_(manager, locations):
        Handle location updates.
    - locationManager_didChangeAuthorizationStatus_(manager, status):
        Handle changes to authorization status.
    - locationManager_didUpdateHeading_(manager, new_heading):
        Handle heading updates.
    """

    def init(self):
        self = objc.super(LocationManagerDelegate, self).init()
        if self is None:
            return None
        self.location = None
        self.heading = None
        return self

    def locationManager_didUpdateLocations_(self, manager, locations):
        """Handle location updates."""
        self.location = locations[-1]
        coordinate = self.location.coordinate()
        logging.info(
            f"Location updated: Latitude = {coordinate.latitude}, Longitude = {coordinate.longitude}"
        )

    def locationManager_didChangeAuthorizationStatus_(self, manager, status):
        """Handle changes to authorization status."""
        if status == kCLAuthorizationStatusAuthorizedAlways:
            logging.info("Location services authorized (Always).")
        elif status == kCLAuthorizationStatusDenied:
            logging.error("Location services denied.")
        elif status == kCLAuthorizationStatusRestricted:
            logging.warning("Location services restricted.")
        elif status == kCLAuthorizationStatusNotDetermined:
            logging.info("Authorization not determined.")

    def locationManager_didUpdateHeading_(self, manager, new_heading):
        """Handle heading updates."""
        self.heading = new_heading.trueHeading
        logging.info(f"Heading updated: {self.heading}°")


# LocationManager to manage location services and integrate with device-place mapping
class LocationManager:
    """
    class LocationManager:

    def __init__(self, event_bus: EventBus):
    """

    def __init__(self, event_bus: EventBus):
        self.manager = CLLocationManager.alloc().init()
        self.delegate = LocationManagerDelegate.alloc().init()
        self.manager.setDelegate_(self.delegate)
        self.place_service = PlaceService()
        self.device_service = DeviceService()

    def request_authorization(self):
        """Request authorization for location services."""
        status = self.manager.authorizationStatus()
        if status == kCLAuthorizationStatusAuthorizedAlways:
            logging.info("Location services already authorized (Always).")
        elif status == kCLAuthorizationStatusNotDetermined:
            logging.info(
                "Requesting 'Always' authorization for location services."
            )
            self.manager.requestAlwaysAuthorization()
        elif status == kCLAuthorizationStatusDenied:
            logging.error("Location services denied by user.")
        elif status == kCLAuthorizationStatusRestricted:
            logging.warning("Location services are restricted.")
        else:
            logging.warning("Unexpected authorization status.")

    def check_location_services(self):
        """Check if location services are enabled."""
        if not CLLocationManager.locationServicesEnabled():
            logging.error("Location services are disabled.")
            return False
        logging.info("Location services are enabled.")
        return True

    def get_current_location(self, timeout=10):
        """Retrieve the current location (latitude, longitude) with a timeout."""
        if not self.check_location_services():
            return None, None

        self.manager.startUpdatingLocation()
        start_time = time.time()
        run_loop = NSRunLoop.currentRunLoop()

        while self.delegate.location is None:
            future_date = NSDate.dateWithTimeIntervalSinceNow_(1)
            run_loop.runMode_beforeDate_(NSDefaultRunLoopMode, future_date)

            if time.time() - start_time > timeout:
                logging.warning("Timeout exceeded while waiting for location.")
                self.manager.stopUpdatingLocation()
                return None, None

        self.manager.stopUpdatingLocation()

        coordinate = self.delegate.location.coordinate()
        return coordinate.latitude, coordinate.longitude

    async def async_get_location(self):
        """Asynchronous method to retrieve the current location."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_current_location)

    def link_device_to_place(self, device_address, device_name):
        """Link a device to a place based on GPS or manual input."""
        lat, lon = self.get_current_location()
        if lat is None and lon is None:
            place = prompt_for_place(
                self.place_service
            )  # Prompt user to create/select place manually
        else:
            place = self.place_service.create_place(
                f"Auto-location for {device_name}", latitude=lat, longitude=lon
            )

        device = self.device_service.create_device(
            device_address, device_name, place.id
        )
        logging.info(f"Device {device_name} linked to place {place.name}.")

    def start_region_monitoring(self, region_id, latitude, longitude, radius):
        """Start monitoring a geographic region."""
        coordinate = CLLocationCoordinate2D(latitude, longitude)
        region = CLRegion.alloc().initWithCircularRegionWithCenter_radius_identifier_(
            coordinate, radius, region_id
        )
        self.manager.startMonitoringForRegion_(region)
        logging.info(f"Started monitoring region: {region_id}")

    def stop_region_monitoring(self, region_id):
        """Stop monitoring a geographic region."""
        regions = self.manager.monitoredRegions()
        for region in regions:
            if region.identifier == region_id:
                self.manager.stopMonitoringForRegion_(region)
                logging.info(f"Stopped monitoring region: {region_id}")

    def start_beacon_ranging(self, uuid_str, region_id):
        """Start ranging beacons in a specified region."""
        uuid = NSUUID.alloc().initWithUUIDString_(uuid_str)
        beacon_region = CLBeaconRegion.alloc().initWithUUID_identifier_(
            uuid, region_id
        )
        self.manager.startRangingBeaconsInRegion_(beacon_region)
        logging.info(f"Started ranging beacons in region: {region_id}")

    def stop_beacon_ranging(self, uuid_str, region_id):
        """Stop ranging beacons in a specified region."""
        uuid = NSUUID.alloc().initWithUUIDString_(uuid_str)
        beacon_region = CLBeaconRegion.alloc().initWithUUID_identifier_(
            uuid, region_id
        )
        self.manager.stopRangingBeaconsInRegion_(beacon_region)
        logging.info(f"Stopped ranging beacons in region: {region_id}")

    def start_heading_updates(self):
        """Start monitoring heading updates."""
        self.manager.startUpdatingHeading()
        logging.info("Started heading updates.")

    def stop_heading_updates(self):
        """Stop monitoring heading updates."""
        self.manager.stopUpdatingHeading()
        logging.info("Stopped heading updates.")

    def get_current_heading(self):
        """Retrieve the current heading."""
        if self.delegate.heading is not None:
            logging.info(f"Current heading: {self.delegate.heading}°")
            return self.delegate.heading
        logging.warning("Heading data not available.")
        return None

    def session(self):
        return self.device_service.session()


def prompt_for_place(place_service):
    """
    :param place_service: An object that provides place-related operations such as listing existing places and creating new places.
    :return: A selected existing place or a newly created place, depending on user input, or None if the input is invalid.
    """
    print(
        "GPS data unavailable. Please select an existing place or create a new one."
    )

    places = place_service.list_places()

    if places:
        print("Existing places:")
        for idx, place in enumerate(places, start=1):
            print(
                f"{idx}. {place.name} (Lat: {place.latitude}, Lon: {place.longitude})"
            )

    choice = (
        input(
            "Select a place by number, or type 'new' to create a new place: "
        )
        .strip()
        .lower()
    )

    if choice == "new":
        name = input("Enter the name of the new place: ")
        latitude = input("Enter latitude (or leave blank for unknown): ")
        longitude = input("Enter longitude (or leave blank for unknown): ")
        description = input("Enter a description (optional): ")
        return place_service.create_place(
            name,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
            description=description,
        )
    else:
        try:
            selected_index = int(choice) - 1
            if 0 <= selected_index < len(places):
                return places[selected_index]
            else:
                print("Invalid selection.")
        except ValueError:
            print("Invalid input.")

    return None


if __name__ == "__main__":
    event_bus = EventBus()
    location_manager = LocationManager(event_bus)
    location_manager.request_authorization()
    lat, long = location_manager.get_current_location(10)
    print(f"lat: {lat}, long: {long}")
