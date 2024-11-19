# Scanners Readme 
## Description
 To update the sequence diagram with the added reporting methods that perform device-to-place analysis, we can modify the existing diagram by adding new interaction steps as follows:

1. The `run_scanner()` command is called from the CLI, starting the BLE scanner application.
2. The application creates instances of `LocationManager`, `EventBus`, and `BLEScanner`.
3. The `LocationManager` requests authorization to access location services (not shown in the provided code).
4. The `BLEScanner` initializes its internal variables and starts scanning for BLE devices in a loop using the `scan()` method.
5. During each iteration of the scan loop, the `scan()` method calls the `discover()` function from the `BleakScanner` library to discover nearby BLE devices.
6. For each discovered device, the `scan()` method processes the device, updates or inserts it into the database, records sightings, manages device-place relationships, and logs relevant information. It also finds places for devices based on their geolocation.
7. Periodically during the scan loop, the `report_places_and_devices()` method is called to generate a report of all places and the devices seen at each place.
8. The process repeats until the user stops the scanner or encounters an error.

```mermaid
sequenceDiagram
participant User
participant CLI
participant LocationManager
participant EventBus
participant BLEScanner

User->>CLI: run_scanner()
CLI->>BLEScanner: initialize(LocationManager, EventBus)
Note over BLEScanner, LocationManager: LocationManager requests authorization (not shown)
BLEScanner->>BLEScanner: _scan_task = asyncio.create_task(self._scan_loop())

repeat for each iteration of the scan loop
    Note over BLEScanner:_scan_task: discovers nearby devices with BleakScanner.discover()
    for each discovered device do:
        BLEScanner->>BLEScanner: processDevice(device)
        BLEScanner->>Database: updateOrInsertDevice(device)
        BLEScanner->>BLEScanner: recordSighting(device, place)
        BLEScanner->>BLEScanner: manageDevicePlaceRelationships(device, place)
        BLEScanner->>BLEScanner: logDeviceInfo(device, place)
    end

    Note over BLEScanner:_scan_task: calls report_places_and_devices() periodically to generate reports
end
Note over BLEScanner:_scan_task: sleeps for 5 seconds before repeating the scan loop
```

Analysis is performed during the scan task.
The `BLEScanner` is responsible for scanning and managing devices during the scan task. The `processDevice()` method is called to process each discovered device, while the `updateOrInsertDevice()` method is calledhree main reporting methods: `report_places_and_devices()`, `report_devices_seen_in_multiple_places()`, and `report_devices_seen_in_multiple_places_with_gatt_check()`.

1. `report_places_and_devices()` - Generates a report of all places and the devices seen at each place.

```mermaid
sequenceDiagram
participant BLEScanner
participant Database

BLEScanner->>Database: Fetch all places with related data eagerly loaded
Note over Database: processes places and their devices
Database-->>BLEScanner: places

for each place in places do:
    BLEScanner->>place: iterate through devices seen at this place
    for each device in devices do:
        BLEScanner->>device: log information about the device
    end
end
```

2. `report_devices_seen_in_multiple_places()` - Generates a report of devices that have been seen at multiple different locations.

```mermaid
sequenceDiagram
participant BLEScanner
participant Database

BLEScanner->>Database: Fetch devices seen in more than one place
Note over Database: processes places and their devices
Database-->>BLEScanner: devices

for each device in devices do:
    BLEScanner->>device: iterate through places where the device has been seen
    for each place in places do:
        BLEScanner->>place: log information about the place and device sighting
    end
end
```

3. `report_devices_seen_in_multiple_places_with_gatt_check()` - Generates a report of devices that have been seen at multiple different locations, considering devices with matching GATT signatures as potentially the same device despite MAC address randomization.

```mermaid
sequenceDiagram
participant BLEScanner
participant Database

BLEScanner->>Database: Fetch Seen records with matching GATT signatures seen at multiple places
Note over Database: organizes seen records by GATT signature and filters distinct places
Database-->>BLEScanner: seen_records grouped by GATT signature

for each GATT signature in seen_records do:
    BLEScanner->>seen_records[GATT signature]: iterate through records for this GATT signature
    for each record in seen_records[GATT signature] do:
        BLEScanner->>device: log information about the device and sighting
    end
end
```