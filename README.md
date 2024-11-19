Here is the updated `README.md` file with event bus subscription and usage:

---

# SWIVEL Framework for Mac and Linux

This framework is designed to provide a common interface for accessing various functionalities provided by the underlying operating system. The specific functionalities supported will depend on the particular version of the operating system being used.

## Contents

* [Getting Started](#getting-started)
* [Documentation](#documentation)
* [Community Support](#community-support))
* [License](#license))

## Purpose and Functionality

The SWIVEL framework is designed for **Counter Intelligence** purposes, specifically to provide a comprehensive picture of Bluetooth Low Energy (BLE) device behavior and movement. The purpose is mapped to the acronym **S.W.I.V.E.L.**, which represents the following components:

*   **S - Scanning**: The framework includes a `BLEScanner` class that scans for BLE devices, which is the first step in counter intelligence.
*   **W - Watching**: The `LocationManager` class is responsible for watching and updating the locations of BLE devices.
*   **I - Identifying**: The `EventBus` class enables identifying and responding to events related to BLE devices, such as when a device is found or a location update occurs.
*   **V - Verifying**: The `PlaceService` class and `DeviceService` class are responsible for verifying the accuracy of location data.
*   **E - Evaluating**: The `WiFiService` class evaluates the presence of nearby Wi-Fi networks and provides methods to list available networks.
*   **L - Linking**: The framework links device information to location data, creating a comprehensive picture of device behavior and movement.

By incorporating these features, the SWIVEL framework provides a robust platform for counter intelligence purposes.

## Event Bus Subscription and Usage

To take full advantage of the SWIVEL framework, you can subscribe to events published by various classes. This allows you to respond to events as they occur, which can be useful for understanding device behavior and movement.


**Usage**

To take full advantage of the SWIVEL framework, you can use it in conjunction with other classes and services. Here is an example of how to use the SWIVEL framework:

```python
from swivel.scanners.ble_scanner import BLEScanner

# Create a new BLEScanner object
scanner = BLEScanner()

# Scan for BLE devices
devices = scanner.scan()
```

## Getting Started
To get started with the SWIVEL Framework

1. Git clone https://github.com/blakdayz/swivel/framework.git
2. Run <code> pip install poetry </code> in terminal
3. Run <code> poetry install </code> in terminal


## Permissions Setup (MacOS Sequoia 15.1)

In order for use to obtain permission and ensure the proper functioning of the LocationManager class, if using this with a python interpreter (ie. <code>python main.py</code>), simply goto System Settings->Privacy and Security->Location Services->Toggle On <code>Python</code>