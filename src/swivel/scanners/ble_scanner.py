import asyncio
import logging
import os
import random
import string
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta

import click
import geopy.distance
from bleak import BleakScanner
from sqlalchemy import select, func, distinct, text
from sqlalchemy.orm import selectinload

from swivel.database.ble_dto import (
    Device,
    Relocation,
    Place,
    PlaceDevice,
    Seen,
    Base,
)
from swivel.database.datastorage_json import AsyncSessionLocal, async_engine
from swivel.events.event_subsystem import EventBus

warnings.filterwarnings("ignore", category=DeprecationWarning)
# At the top of the file
logging.basicConfig(
    filename="bluetooth.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# Data class to hold geolocation data
@dataclass
class GeoData:
    """
    Represents geographical data.

    Attributes:
        latitude (float): The latitude of the geographic location.
        longitude (float): The longitude of the geographic location.
    """

    latitude: float
    longitude: float


# Function to create database tables
async def create_tables():
    """
    Creates database tables using the provided asynchronous engine.

    :return: None
    """
    async with async_engine.begin() as conn:
        logging.info(
            f"Creating database tables... (Using engine: {async_engine})"
        )
        await conn.run_sync(Base.metadata.create_all)
        logging.info("Database tables created.")

        # Check if using a file-based SQLite database, log the file path
        db_url = str(async_engine.url)
        if "sqlite" in db_url:
            db_path = db_url.split("///")[-1]
            if os.path.exists(db_path):
                logging.info(f"SQLite database file located at: {db_path}")
            else:
                logging.error(f"SQLite database file NOT found at: {db_path}")

    logging.info("Database connection remains open.")


# Function to list database tables
async def list_tables():
    """
    Fetches and lists all table names from the SQLite database.

    :return: A list of tuples where each tuple contains the name of a table in the database.
    """
    async with async_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table';")
        )
        tables = result.fetchall()
        logging.info(
            f"Tables in the database: {[table[0] for table in tables]}"
        )
        return tables


class BLEScanner:
    """
    Class for scanning Bluetooth Low Energy (BLE) devices and managing their sightings.

    DEFAULT_PLACE_RADIUS
        Default radius in meters used to define a "place".

    Args:
        location_manager: Manages and provides location data.
        event_bus: Event bus for publishing events.

    Attributes:
        _devices: Dictionary to keep track of discovered devices.
        location_manager: Instance of location manager.
        event_bus: Instance of event bus.
        cached_geodata: Cached geolocation data.
        last_gps_fetch: Timestamp of the last geolocation fetch.
    """

    DEFAULT_PLACE_RADIUS = 50.0  # in meters

    def __init__(self, location_manager, event_bus):
        self._scan_task = None
        self._devices = {}
        self._is_scanning = False
        self.location_manager = location_manager
        self.event_bus = event_bus
        self.cached_geodata = None
        self.last_gps_fetch = datetime.min

    async def scan(self):
        """
        :summary: Scans for Bluetooth devices, updates the device database, and logs the results.

        :description: Initiates a Bluetooth scan using the BleakScanner library, processes the discovered devices by updating or inserting into the database. It records device sightings, manages device place relationships, and logs the final count of new, relocated, and total devices.

        :raises Exception: If an error occurs during scanning or database operations.

        :return: None
        """
        try:
            logging.info("Scanning for Bluetooth devices...")
            geodata = await self._get_cached_geodata()
            devices = (
                await BleakScanner.discover()
            )  # Perform the Bluetooth scan

            new_devices_count = 0
            existing_in_same_place_count = 0
            relocated_devices_count = 0
            relocations_count = 0

            async with AsyncSessionLocal() as session:
                for device in devices:
                    device_address = device.address
                    device_name = device.name or "Unknown"
                    advertisement_data = device.metadata.get(
                        "advertisement_data", {}
                    )
                    rssi = (
                        advertisement_data.rssi
                        if "rssi" in advertisement_data
                        else device.rssi
                    )
                    uuids = (
                        advertisement_data.service_uuids
                        if "service_uuids" in advertisement_data
                        else device.metadata.get("uuids", [])
                    )
                    gatt_signature = ",".join(uuids) if uuids else None

                    try:
                        # Check if the device already exists
                        result = await session.execute(
                            select(Device).filter_by(id=device_address)
                        )
                        existing_device = result.scalars().first()

                        if existing_device:
                            # Device exists, update times_seen and last_seen
                            existing_device.times_seen += 1
                            existing_device.last_seen = datetime.utcnow()
                            # Check if device is in the same place
                            place = await self._find_place_for_device(
                                session, geodata
                            )
                            if place:
                                # Check if the device is in the same place
                                result = await session.execute(
                                    select(PlaceDevice).filter_by(
                                        place_id=place.id,
                                        device_id=existing_device.id,
                                    )
                                )
                                place_device = result.scalars().first()

                                if place_device:
                                    # Device is in the same place
                                    place_device.times_seen += 1
                                    existing_in_same_place_count += 1
                                else:
                                    # Device relocated to a new place
                                    await self._update_place_device(
                                        session, place, existing_device
                                    )
                                    await self._update_relocation(
                                        session, existing_device, geodata
                                    )
                                    relocated_devices_count += 1
                                    relocations_count += 1
                            else:
                                # Device is in a new place
                                new_place = await self._create_new_place(
                                    session, geodata
                                )
                                await self._add_device_to_place(
                                    session, new_place, existing_device
                                )
                                await self._update_relocation(
                                    session, existing_device, geodata
                                )
                                relocated_devices_count += 1
                                relocations_count += 1
                        else:
                            # New device
                            new_device = Device(
                                id=device_address,
                                name=device_name,
                                address=device_address,
                                geodata=f"{geodata.latitude}, {geodata.longitude}",
                                times_seen=1,
                                first_seen=datetime.utcnow(),
                                last_seen=datetime.utcnow(),
                            )
                            session.add(new_device)
                            await session.flush()  # Ensure device.id is available
                            place = await self._find_place_for_device(
                                session, geodata
                            )
                            if not place:
                                place = await self._create_new_place(
                                    session, geodata
                                )
                            await self._add_device_to_place(
                                session, place, new_device
                            )
                            new_devices_count += 1

                        # Record the Seen entry
                        await self._record_seen(
                            session,
                            device_address,
                            place.id,
                            rssi,
                            gatt_signature,
                        )
                    except Exception as e:
                        await session.rollback()
                        logging.error(
                            f"Error processing device {device_address}: {e}"
                        )

                await session.commit()  # Commit all changes at once

            total_devices = len(devices)
            logging.info(f"Discovered {total_devices} devices.")
            logging.info(
                f"New devices: {new_devices_count}, Devices in same place: {existing_in_same_place_count}, Relocated devices: {relocated_devices_count}, Total relocations: {relocations_count}"
            )
        except Exception as e:
            logging.error(f"Error during scanning: {e}")

    async def _scan_loop(self):
        try:
            while self._is_scanning:
                await self.scan()
                await asyncio.sleep(5)  # Adjust the sleep duration as needed
        except asyncio.CancelledError:
            pass  # Handle task cancellation
        except Exception as e:
            logging.error(f"Scanner encountered an error: {e}")
            self._is_scanning = False
            # Publish an error event
            self.event_bus.publish("scanner_error", str(e))

    async def _get_cached_geodata(self) -> GeoData:
        """
        Fetches geodata, using cached data if the last fetch was recent.
        :return: GeoData
        """
        if datetime.utcnow() - self.last_gps_fetch > timedelta(minutes=1):
            (
                lat,
                lon,
            ) = self.location_manager.get_current_location()  # Removed 'await'
            self.cached_geodata = GeoData(latitude=lat, longitude=lon)
            self.last_gps_fetch = datetime.utcnow()
        return self.cached_geodata

    @staticmethod
    async def _find_place_for_device(session, geodata):
        """
        Finds a place where the current geodata is within the BLE scan radius.
        :param session: Database session.
        :param geodata: Current geolocation data.
        :return: A Place instance or None if no suitable place is found.
        """
        try:
            # Fetch all places
            result = await session.execute(select(Place))
            places = result.scalars().all()

            for place in places:
                distance_between = geopy.distance.distance(
                    (geodata.latitude, geodata.longitude),
                    (place.latitude, place.longitude),
                ).meters

                if distance_between <= place.radius:
                    return place
            return None
        except Exception as e:
            logging.error(f"Error finding place for device: {e}")
            return None

    async def _create_new_place(self, session, geodata):
        """
        Creates a new place if no existing place is within range.
        :param session: Database session.
        :param geodata: Current geolocation data.
        :return: The newly created Place instance.
        """
        try:
            new_place = Place(
                latitude=geodata.latitude,
                longitude=geodata.longitude,
                radius=self.DEFAULT_PLACE_RADIUS,
            )
            session.add(new_place)
            await session.commit()
            logging.info(
                f"Created a new place at {geodata.latitude}, {geodata.longitude} with radius {self.DEFAULT_PLACE_RADIUS} meters"
            )
            return new_place
        except Exception as e:
            await session.rollback()
            logging.error(f"Error creating new place: {e}")
            return None

    @staticmethod
    async def fetch_rssi_data(device_id):
        """Fetch RSSI data for a device from the Seen table."""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Seen).filter_by(device_id=device_id)
                )
                seen_records = result.scalars().all()
                return [(seen.timestamp, seen.rssi) for seen in seen_records]
        except Exception as e:
            logging.error(
                f"Error fetching RSSI data for device {device_id}: {e}"
            )
            return []

    @staticmethod
    async def _update_place_device(session, place: Place, device: Device):
        """
        Updates the record for a device seen in a place, increasing the times_seen count.
        :param session: Database session.
        :param place: The Place where the device was seen.
        :param device: The Device instance.
        :return: None
        """
        try:
            result = await session.execute(
                select(PlaceDevice).filter_by(
                    place_id=place.id, device_id=device.id
                )
            )
            place_device = result.scalars().first()

            if place_device:
                place_device.times_seen += 1
                logging.info(
                    f"Device {device.id} seen {place_device.times_seen} times at {place.name or 'Unnamed Place'}."
                )
            else:
                place_device = PlaceDevice(
                    place_id=place.id, device_id=device.id, times_seen=1
                )
                session.add(place_device)
                logging.info(
                    f"Device {device.id} added to place {place.name or 'Unnamed Place'}."
                )
            device.last_seen = datetime.utcnow()
            await session.commit()
        except Exception as e:
            await session.rollback()
            logging.error(f"Error updating place device: {e}")

    @staticmethod
    async def _add_device_to_place(session, place, device):
        """
        Adds a new device to a place.
        :param session: Database session.
        :param place: The Place instance.
        :param device: The new Device instance.
        :return: None
        """
        try:
            place_device = PlaceDevice(
                place_id=place.id, device_id=device.id, times_seen=1
            )
            session.add(place_device)
            logging.info(
                f"Device {device.id} added to place {place.name or 'Unnamed Place'}."
            )
            await session.commit()
        except Exception as e:
            await session.rollback()
            logging.error(f"Error adding device to place: {e}")

    @staticmethod
    async def _update_relocation(session, device, new_geodata: GeoData):
        """
        Updates the device relocation in the database.
        :param session: Database session used for executing queries.
        :param device: The existing device to be updated.
        :param new_geodata: The new geolocation data.
        :return: None
        """
        try:
            logging.info(f"Updating device relocation: {device.id}")
            relocation = Relocation(
                device_id=device.id,
                old_geodata=device.geodata,
                new_geodata=f"{new_geodata.latitude}, {new_geodata.longitude}",
                timestamp=datetime.utcnow(),
            )
            session.add(relocation)
            device.geodata = f"{new_geodata.latitude}, {new_geodata.longitude}"
            await session.commit()
            logging.info(
                f"Device {device.id} relocated from {relocation.old_geodata} to {relocation.new_geodata}"
            )
        except Exception as e:
            await session.rollback()
            logging.error(f"Database error during relocation update: {e}")

    async def fetch_shared_devices(self, session, with_gatt_check=False):
        """
        Fetch devices that have been seen in multiple places.
        Optionally apply GATT signature check for MAC address randomization.
        """
        try:
            if with_gatt_check:
                # Query to group devices by GATT signature, considering multiple locations
                gatt_subquery = (
                    select(Seen.gatt_signature)
                    .where(Seen.gatt_signature.isnot(None))
                    .group_by(Seen.gatt_signature)
                    .having(func.count(distinct(Seen.place_id)) > 1)
                    .subquery()
                )

                result = await session.execute(
                    select(Seen)
                    .options(
                        selectinload(Seen.device), selectinload(Seen.place)
                    )
                    .filter(Seen.gatt_signature.in_(gatt_subquery))
                )
                seen_records = result.scalars().all()

                # Process the results into a dictionary of devices and their places
                shared_devices = {}
                for record in seen_records:
                    device = record.device
                    place = record.place
                    if device.id not in shared_devices:
                        shared_devices[device.id] = {
                            "device": device,
                            "places": [],
                        }
                    shared_devices[device.id]["places"].append(place)

                return shared_devices

            else:
                # Query to fetch devices seen in more than one place
                subquery = (
                    select(PlaceDevice.device_id)
                    .group_by(PlaceDevice.device_id)
                    .having(func.count(PlaceDevice.place_id) > 1)
                    .subquery()
                )

                result = await session.execute(
                    select(Device)
                    .options(selectinload(Device.places))
                    .filter(Device.id.in_(subquery))
                )
                devices = result.scalars().all()

                # Process devices and their places
                shared_devices = {}
                for device in devices:
                    shared_devices[device.id] = {
                        "device": device,
                        "places": [pd.place for pd in device.places],
                    }

                return shared_devices

        except Exception as e:
            logging.error(f"Error fetching shared devices: {e}")
            return {}

    @staticmethod
    async def _record_seen(session, device_id, place_id, rssi, gatt_signature):
        """
        Records a 'Seen' entry for the device.
        :param session: Database session.
        :param device_id: ID of the device.
        :param place_id: ID of the place.
        :param rssi: RSSI value.
        :param gatt_signature: GATT service signatures.
        :return: None
        """
        try:
            seen_record = Seen(
                device_id=device_id,
                place_id=place_id,
                timestamp=datetime.utcnow(),
                rssi=rssi,
                gatt_signature=gatt_signature,
            )
            session.add(seen_record)
            logging.info(
                f"Recorded 'Seen' entry for device {device_id} at place {place_id}"
            )
        except Exception as e:
            await session.rollback()
            logging.error(f"Error recording 'Seen' entry: {e}")

    async def report_places_and_devices(self):
        """
        Generates a report of all places and the devices seen at each place.
        """
        try:
            async with AsyncSessionLocal() as session:
                # Fetch all places with related data eagerly loaded
                result = await session.execute(
                    select(Place).options(
                        selectinload(Place.devices)
                        .selectinload(PlaceDevice.device)
                        .selectinload(Device.seen_records)
                    )
                )
                places = result.scalars().all()  # Removed 'await' here

                for place in places:
                    place_name = (
                        place.name
                        or f"Unnamed Place ({place.latitude}, {place.longitude})"
                    )
                    logging.info(f"Place: {place_name}")
                    place_devices = (
                        place.devices
                    )  # List of PlaceDevice instances

                    for pd in place_devices:
                        device = pd.device  # Device instance
                        device_name = device.name or "Unknown Device"
                        logging.info(f"  Device: {device_name} ({device.id})")
                        logging.info(
                            f"    Times seen at this place: {pd.times_seen}"
                        )

                        # Filter seen_records for this device at this place
                        seen_records = [
                            s
                            for s in device.seen_records
                            if s.place_id == place.id
                        ]
                        for seen in seen_records:
                            logging.info(
                                f"      Seen at {seen.timestamp}, RSSI: {seen.rssi}, GATT: {seen.gatt_signature}"
                            )
        except Exception as e:
            logging.error(f"Error generating report: {e}")

    async def report_devices_seen_in_multiple_places(self):
        """
        Generates a report of devices that have been seen at multiple different locations.
        """
        try:
            async with AsyncSessionLocal() as session:
                # Subquery to find device_ids seen in more than one place
                subquery = (
                    select(PlaceDevice.device_id)
                    .group_by(PlaceDevice.device_id)
                    .having(func.count(PlaceDevice.place_id) > 1)
                    .subquery()
                )

                # Query devices that have been seen in multiple places
                result = await session.execute(
                    select(Device)
                    .options(
                        selectinload(Device.places).selectinload(
                            PlaceDevice.place
                        )
                    )
                    .filter(Device.id.in_(subquery))
                )
                devices = result.scalars().all()

                if not devices:
                    logging.info(
                        "No devices have been seen at multiple locations."
                    )
                    return

                for device in devices:
                    device_name = device.name or "Unknown Device"
                    logging.info(f"Device: {device_name} ({device.id})")
                    places = [pd.place for pd in device.places]
                    for place in places:
                        place_name = (
                            place.name
                            or f"Unnamed Place ({place.latitude}, {place.longitude})"
                        )
                        logging.info(f"  Seen at place: {place_name}")
        except Exception as e:
            logging.error(
                f"Error generating multi-location devices report: {e}"
            )

    async def start_scanning(self):
        """
        Starts the scanning process.
        """
        if not self._is_scanning:
            self._is_scanning = True
            self._scan_task = asyncio.create_task(self._scan_loop())
            logging.info("Scanner started.")

    async def stop_scanning(self):
        """
        Stops the scanning process.
        """
        if self._is_scanning and self._scan_task:
            self._is_scanning = False
            self._scan_task.cancel()
            try:
                await self._scan_task
            except asyncio.CancelledError:
                logging.info("Scanner stopped.")
            self._scan_task = None

    async def _scan_loop_asycio(self):
        """
        The scanning loop that runs continuously.
        """
        try:
            while self._is_scanning:
                await self.scan()
                await asyncio.sleep(5)  # Adjust the sleep duration as needed
        except asyncio.CancelledError:
            pass  # Handle task cancellation
        except Exception as e:
            logging.error(f"Scanner encountered an error: {e}")
            # You may want to report this error back to the GUI
            self._is_scanning = False
            raise e  # Reraise the exception for handling

    def is_running(self):
        """
        Returns True if the scanner is running.
        """
        return self._is_scanning

    @staticmethod
    async def report_devices_seen_in_multiple_places_with_gatt_check():
        """
        Generates a report of devices that have been seen at multiple different locations,
        considering devices with matching GATT signatures as potentially the same device
        despite MAC address randomization.
        """
        try:
            async with AsyncSessionLocal() as session:
                # Subquery to find GATT signatures seen in more than one place
                gatt_subquery = (
                    select(Seen.gatt_signature)
                    .where(Seen.gatt_signature.isnot(None))
                    .group_by(Seen.gatt_signature)
                    .having(func.count(distinct(Seen.place_id)) > 1)
                    .subquery()
                )

                # Query Seen records with GATT signatures seen at multiple places
                result = await session.execute(
                    select(Seen)
                    .options(
                        selectinload(Seen.device), selectinload(Seen.place)
                    )
                    .filter(Seen.gatt_signature.in_(gatt_subquery))
                    .order_by(Seen.gatt_signature)
                )
                seen_records = result.scalars().all()

                if not seen_records:
                    logging.info(
                        "No devices with matching GATT signatures have been seen at multiple locations."
                    )
                    return

                # Organize seen records by GATT signature
                from collections import defaultdict

                gatt_groups = defaultdict(list)
                for seen in seen_records:
                    gatt_groups[seen.gatt_signature].append(seen)

                for gatt_signature, records in gatt_groups.items():
                    # Get distinct places
                    places = {record.place for record in records}
                    if len(places) > 1:
                        logging.info(
                            f"Devices with GATT signature '{gatt_signature}' have been seen at multiple locations:"
                        )
                        for record in records:
                            device = record.device
                            device_name = device.name or "Unknown Device"
                            place = record.place
                            place_name = (
                                place.name
                                or f"Unnamed Place ({place.latitude}, {place.longitude})"
                            )
                            logging.info(
                                f"  Device ID: {device.id}, Name: {device_name}"
                            )
                            logging.info(
                                f"    Seen at place: {place_name} on {record.timestamp}"
                            )
                    else:
                        # Devices with this GATT signature have only been seen at one place
                        pass  # We can skip these
        except Exception as e:
            logging.error(
                f"Error generating devices report with GATT signature check: {e}"
            )

    @staticmethod
    async def recreate_database():
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)  # Drop all tables
            await conn.run_sync(Base.metadata.create_all)  # Recreate tables
            logging.info("Database recreated.")


@click.group()
def cli():
    """
    :return: None
    """
    pass


@cli.command()
def recreate_db():
    """
    Recreates the database, auto-backing up the current.

    :return: None
    """
    import asyncio

    async def recreate():
        file = "bluetooth_devices.db"
        if os.path.exists(file):
            # pick a random file name
            random_nanoid = "".join(
                random.choices(string.ascii_letters + string.digits, k=8)
            )
            os.rename(file, f"{file}.bak.{random_nanoid}")

        from swivel.location.location_manager import LocationManager

        event_bus = EventBus()
        location_manager = LocationManager(event_bus)
        location_manager.request_authorization()
        ble_scanner = BLEScanner(location_manager, event_bus)
        await ble_scanner.recreate_database()
        print("Recreated database")

    asyncio.run(recreate())


@cli.command()
def run_scanner():
    """
    Starts the BLE scanner application and enters a
    scan loop.

    :return: None
    """
    import asyncio

    async def run():
        from swivel.location.location_manager import LocationManager

        logging.info("Starting the BLE scanner application...")
        event_bus = EventBus()
        location_manager = LocationManager(event_bus)
        location_manager.request_authorization()
        ble_scanner = BLEScanner(location_manager, event_bus)

        # Start scanning in a loop
        while True:
            await ble_scanner.scan()
            await asyncio.sleep(5)  # Adjust the sleep duration as needed

    asyncio.run(run())


if __name__ == "__main__":
    cli()
