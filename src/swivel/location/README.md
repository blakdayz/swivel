# SWIVEL LocationManager Readme
## A direct calling, asynchronous self authorizing, no prompting script to get the location from CoreLocation

Utilizes the MacOS CoreLocation API to manage and retrieve the user's current location, heading, and other related geolocation data. This script is a part of a larger project named Swivel, and it leverages Objective-C bindings for interacting with Core Location services.

Here's a brief walkthrough of the code:

Imports necessary Python libraries (time, asyncio, objc, logging) as well as CoreLocation modules from the <code>CoreLocation</code> package and Foundation modules from the Foundation module.

Defines a LocationManagerDelegate class that acts as a delegate for handling location updates. This class is an NSObject subclass that implements methods to handle location, heading updates, and changes in authorization status.

Creates the main LocationManager class which manages location services and integrates with device-place mapping. It initializes a CLLocationManager object, sets up its delegate as the previously defined LocationManagerDelegate instance, and creates PlaceService and DeviceService objects to manage places and devices respectively. The LocationManager class has several methods for requesting authorization, checking if location services are enabled, retrieving the current location (with a timeout), linking a device to a place based on GPS or manual input, starting region monitoring, stopping region monitoring, starting beacon ranging, stopping beacon ranging, starting heading updates, stopping heading updates, and retrieving the current heading.

Defines an async_get_location method within the LocationManager class which is an asynchronous version of the get_current_location method. This method uses asyncio's event loop to run the get_current_location function concurrently.

Implements a prompt_for_place function that prompts the user to create or select an existing place if GPS data is unavailable.

Finally, the script initializes an EventBus object and a LocationManager instance with the created event bus, requests authorization for location services, retrieves the current location using the get_current_location method (or the async_get_location method in an asynchronous context), and prints the latitude and longitude values.

UML (Unified Modeling Language) process diagram that represents the workflow of the provided `LocationManager` class:
```mermaid
sequenceDiagram
    participant User
    participant LocationManager as Manager
    participant PlaceService as PS
    participant DeviceService as DS
    participant CLLocationManager as CLM
    
    User->>Manager: Initialize LocationManager
    alt Python setup is complete
        Manager->>CLM: Request authorization
    end
    alt Authorization status is NotDetermined or AuthorizedAlways
        Manager->>CLM: Start updating location
        CLM->>Manager: Location update
        Manager->>User: Log location information
    else Authorization status is Denied, Restricted or timeout exceeded
        Manager->>User: Handle authorization denial or timeout
    end
    User->>Manager: Link device to place
    alt Manual input or existing place selection
        Manager->>PS: List places
        User->>Manager: Select place or create new place
    end
    alt Existing place selection
        Manager->>PS: Get selected place
        Manager->>DS: Create device record with place ID
    else Manual input
        Manager->>PS: Create new place with user input
        Manager->>DS: Create device record with new place ID
    end
    User->>Manager: Start region monitoring or beacon ranging
    Manager->>CLM: Start monitoring region/beacons
    Manager->>User: Log monitoring action
    User->>Manager: Stop region monitoring or beacon ranging
    Manager->>CLM: Stop monitoring region/beacons
    Manager->>User: Log stopping action
    User->>Manager: Start/Stop heading updates
    Manager->>CLM: Start/stop updating heading
    Manager->>User: Log heading information
```
1. The user initializes the `LocationManager` class, which sets up necessary components like `PlaceService`, `DeviceService`, and the CLLocationManager delegate.
2. If authorization is not yet determined or authorized (always), the `LocationManager` requests authorization from the user.
3. Upon receiving authorization, the `LocationManager` starts updating the user's location. When a new location update is received, the `LocationManager` logs the latitude and longitude information.
4. If authorization is denied, restricted, or a timeout occurs, the `LocationManager` notifies the user about the failure.
5. The user can request to link a device to a place. Depending on the user's input, they can either select an existing place or create a new one.
6. If an existing place is selected, the `LocationManager` retrieves the selected place from the `PlaceService` and creates a corresponding device record with the place ID in the `DeviceService`.
7. If a new place is created, the `LocationManager` uses user input to create a new place through the `PlaceService` and then creates a device record associated with the new place ID using the `DeviceService`.
8. The user can initiate region monitoring or beacon ranging. Upon receiving these commands, the `LocationManager` starts monitoring regions or beacons using CLRegion and CLBeaconRegion objects, and logs the action.
9. Similarly, the user can stop region monitoring or beacon ranging, which prompts the `LocationManager` to stop monitoring and log the stopping action.
10. The user can request to start or stop heading updates. The `LocationManager` relays these commands to CLLocationManager for starting or stopping heading updates and logs the respective information.
