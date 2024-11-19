# SWIVEL Framework for Mac 

This framework is designed to provide a common bus interface for automated Bluetooth Low Energy, Wireless, and GPS Signals Collection and Analysis for advanced counter surveillance operations. 

## Contents

* [Getting Started](#getting-started)
* [Documentation](#documentation)
* [Community Support](#community-support))
* [License](#license))

## How to Use 

1. Download the repo and set your location services in MacOS (System Settings->Privacy and Security->Location Services->Python (turn it on))
2. Open terminal to the project location root and run <code>chmod +x ./first_run.sh && ./first_run.sh</code>
3. After wards, running <code>start_service.sh</code> will launch the scanners and web services.
4. Navigate to http://127.0.0.1:8000/docs to explore the endpoints. Currently Bluetooth_Log and Get_Location are full working.
5. There is a tremenmdous amount of implemented functionality inside - take a look as automated device tracking, and further RSSI based analysis is done but is purposefully left out of this readme as a bar of entry. Enjoy.



## Getting Started
To get started developing locally with the SWIVEL Framework

1. Run <code> git clone https://github.com/blakdayz/swivel && cd ./swivel </code>
2. Run <code> pip install poetry </code> in terminal
3. Run <code> poetry install </code> in terminal


### Notes:

1. Permissions Setup (MacOS Sequoia 15.1) is required first for this to work. 

2. You can run "python src/swivel/scanners/ble_scanner.py --help" from the project root directory to see more options regarding database management and place and location managment. The event bus is operational, and subscriber usage is described in the respective classes.
