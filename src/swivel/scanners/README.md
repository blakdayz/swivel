# SWIVEL Scanners Readme 
## Description

This SWIVEL module performs Bluetooth Low Energy Device Detection, GATT Stack Signature Generation, Tracking, and Analysis

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

loop for each iteration of the scan loop
    Note over BLEScanner: Discovers nearby devices with BleakScanner.discover()
    loop for each discovered device
        BLEScanner->>BLEScanner: processDevice(device)
        BLEScanner->>Database: updateOrInsertDevice(device)
        BLEScanner->>BLEScanner: recordSighting(device, place)
        BLEScanner->>BLEScanner: manageDevicePlaceRelationships(device, place)
        BLEScanner->>BLEScanner: logDeviceInfo(device, place)
    end
    BLEScanner->>BLEScanner: report_places_and_devices() periodically
    BLEScanner->>BLEScanner: sleep for 5 seconds before repeating
end
```

Analysis is performed during the scan task.
The `BLEScanner` is responsible for scanning and managing devices during the scan task. The `processDevice()` method is called to process each discovered device, while the `updateOrInsertDevice()` method is calledhree main reporting methods: `report_places_and_devices()`, `report_devices_seen_in_multiple_places()`, and `report_devices_seen_in_multiple_places_with_gatt_check()`.

1. `report_places_and_devices()` - Generates a report of all places and the devices seen at each place.

```mermaid
sequenceDiagram
    participant ReportGenerator
    participant AsyncSessionLocal
    participant Database
    participant Place
    participant PlaceDevice
    participant Device
    participant Seen

    ReportGenerator->>AsyncSessionLocal: Start async session
    AsyncSessionLocal->>Database: Execute query to fetch places and related data
    Database-->>AsyncSessionLocal: Return places with devices and seen records

    AsyncSessionLocal->>ReportGenerator: Return places

    Note over ReportGenerator: Log places and devices seen at each place
    ReportGenerator->>Place: Retrieve place details
    Place-->>ReportGenerator: Return place details
    ReportGenerator->>PlaceDevice: Retrieve devices associated with the place
    PlaceDevice-->>ReportGenerator: Return PlaceDevice instances
    ReportGenerator->>Device: Retrieve device details
    Device-->>ReportGenerator: Return device details
    ReportGenerator->>Device: Retrieve seen records for the device
    Device-->>ReportGenerator: Return seen records
    ReportGenerator->>Seen: Retrieve seen record details for each device at each place
    Seen-->>ReportGenerator: Return seen record details

    ReportGenerator->>ReportGenerator: Log place and device information
    ReportGenerator->>ReportGenerator: Log times seen, timestamp, RSSI, and GATT signature

    alt Error during process
        ReportGenerator->>ReportGenerator: Log error message
    end
```

2. `report_devices_seen_in_multiple_places()` - Generates a report of devices that have been seen at multiple different locations.

```mermaid
sequenceDiagram
    participant BLEScanner
    participant AsyncSessionLocal
    participant Database
    participant Device
    participant PlaceDevice
    participant Place

    BLEScanner->>AsyncSessionLocal: Start async session
    AsyncSessionLocal->>Database: Execute subquery to find devices seen in multiple places
    Database-->>AsyncSessionLocal: Return device IDs
    AsyncSessionLocal->>Database: Execute main query to fetch devices with matching IDs
    Database-->>AsyncSessionLocal: Return Device records

    AsyncSessionLocal->>BLEScanner: Return devices

    Note over BLEScanner: Log devices and places seen at multiple locations
    BLEScanner->>Device: Retrieve device details for each seen record
    Device-->>BLEScanner: Return device details
    BLEScanner->>PlaceDevice: Retrieve associated places for each device
    PlaceDevice-->>BLEScanner: Return place details
    BLEScanner->>Place: Retrieve place details
    Place-->>BLEScanner: Return place details

    BLEScanner->>BLEScanner: Log device and place information

    alt No devices seen in multiple places
        BLEScanner->>BLEScanner: Log "No devices have been seen at multiple locations."
    end

    alt Error during process
        BLEScanner->>BLEScanner: Log error message
    end

```

3. `report_devices_seen_in_multiple_places_with_gatt_check()` - Generates a report of devices that have been seen at multiple different locations, considering devices with matching GATT signatures as potentially the same device despite MAC address randomization.

```mermaid
sequenceDiagram
    participant BLEScanner
    participant AsyncSessionLocal
    participant Database
    participant Seen
    participant Device
    participant Place

    BLEScanner->>AsyncSessionLocal: Start async session
    AsyncSessionLocal->>Database: Execute subquery to find GATT signatures in multiple places
    Database-->>AsyncSessionLocal: Return GATT signatures
    AsyncSessionLocal->>Database: Execute main query to fetch Seen records with matching GATT signatures
    Database-->>AsyncSessionLocal: Return Seen records with GATT signatures
    AsyncSessionLocal->>BLEScanner: Return seen records

    Note over BLEScanner: Group seen records by GATT signature
    BLEScanner->>BLEScanner: Organize seen records by GATT signature
    Note over BLEScanner: Log devices and places seen at multiple locations
    BLEScanner->>Device: Retrieve device details for each seen record
    Device-->>BLEScanner: Return device details
    BLEScanner->>Place: Retrieve place details for each seen record
    Place-->>BLEScanner: Return place details
    BLEScanner->>BLEScanner: Log device and place information

    alt No records with matching GATT signatures
        BLEScanner->>BLEScanner: Log "No devices with matching GATT signatures"
    end

    alt Error during process
        BLEScanner->>BLEScanner: Log error message
    end
```
