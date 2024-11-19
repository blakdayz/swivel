import asyncio
from email.policy import default

import uvicorn
from fastapi import FastAPI, HTTPException
import json
import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.util import await_only

from src.swivel.scanners.ble_scanner import (
    BLEScanner,
    run_scanner,
    create_tables,
)
from src.swivel.database.datastorage_json import AsyncSessionLocal
from src.swivel.location.location_manager import LocationManager
from src.swivel.events.event_subsystem import EventBus
from swivel.database.ble_dto import Device

app = FastAPI()

event_bus = EventBus()
location_manager = LocationManager(event_bus)
ble_scanner = BLEScanner(location_manager, event_bus)


async def start_scanning():
    await ble_scanner.start_scanning()
    logging.info("BLE Scanner started.")


def stop_scanning():
    ble_scanner.stop_scanning()
    logging.info("BLE Scanner stopped.")


def get_status():
    is_running = ble_scanner.is_running()
    logging.info(f"Request for status received and status is: {is_running}")
    return is_running


@app.get("/get_location/{timeout}")
async def get_location(timeout: int = 10):
    """
    Return the current location
    :param timeout: In Seconds (Default is 10 seconds)
    :type timeout: int
    :return:
    """

    event_bus = EventBus()
    location_manager = LocationManager(event_bus)
    lat, long = location_manager.get_current_location(timeout)
    return json.dumps(f"lat: {lat}, long: {long}")


@app.get("/bluetooth_log")
async def read_bluetooth_log():
    with open("bluetooth.log", "r") as f:
        lines = [line for line in f]
    return json.dumps(lines)


@app.post("/recreate_database")
async def recreate_database_endpoint():
    try:
        recreate_db()
        return {"message": "Database recreated successfully"}
    except Exception as e:
        logging.error(f"Error recreating database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def recreate_db():
    """
    Recreates the database, auto-backing up the current.

    :return: None
    """
    # Remove this line if you don't want to automatically run database recreation when using CLI command
    asyncio.run(ble_scanner.recreate_database())


def create_db():
    """
    Creates the backend database which hosts the device, location, and seen records
    :return:
    """
    return create_tables()


@app.post("/database/create")
async def create_tables():
    """
    Creates the necessary tables, does nothing if things are in order. If things seem broke. Run this and a recreate.
    :return:
    """
    try:
        await create_db()
        return True
    except Exception as e:
        logging.error(f"Error creating database tables: {e}")


@app.post("/scanning/start")
async def start_scanner():
    """
    Starts the BLE Scanner
    :return: True if it started, or error message if it did not
    """
    try:
        await start_scanning()
        return True
    except Exception as e:
        logging.error(e)
        return False


@app.get("/status")
async def get_scanner_status():
    """
    Returns a bool if the scanner reports is_running (regularly scanning)
    :return:
    """
    return get_status()


@app.get("/report/multiple_places")
async def report_multiple_places():
    """
    Returns a JSON string containing details about devices seen at multiple places.

    :return: A JSON string with the list of devices seen at multiple places and their respective locations.
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Device).options(selectinload(Device.places))
            )
            devices = result.scalars().all()

            device_reports = []
            for device in devices:
                device_name = device.name or "Unknown Device"
                places = [
                    f"{place.name} ({place.latitude}, {place.longitude})"
                    for place in device.places
                ]
                report_entry = f"Device: {device_name} ({device.id}), Seen at {', '.join(places)}"
                device_reports.append(report_entry)

            return json.dumps(device_reports)
    except Exception as e:
        logging.error(f"Error generating multiple places report: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/report/multiple_places_with_gatt_check")
async def report_multiple_places_with_gatt_check():
    """
    Returns a JSON string containing details about devices with matching GATT signatures seen at multiple places.

    :return: A JSON string with the list of devices with matching GATT signatures, their respective locations, and timestamps.
    """
    try:
        async with AsyncSessionLocal() as session:
            reports = (
                await ble_scanner.report_devices_seen_in_multiple_places_with_gatt_check()
            )
            return json.dumps(reports)
    except Exception as e:
        logging.error(
            f"Error generating multiple places report with GATT signature check: {e}"
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


if __name__ == "__main__":
    asyncio.run(
        start_scanning()
    )  # Start the BLE scanner upon starting the application
    uvicorn.run(app=app, host="0.0.0.0", port=8000)
