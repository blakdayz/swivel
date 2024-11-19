# SWIVEL Framework for Mac and Linux

This framework is designed to provide a common interface for accessing various functionalities provided by the underlying operating system. The specific functionalities supported will depend on the particular version of the operating system being used.

## Contents

* [Getting Started](#getting-started)
* [Documentation](#documentation)
* [Community Support](#community-support))
* [License](#license))

## How to Use 

1. Install swivel: <code>pip install swivel</code>
2. Import the SWIVEL library.
```python
import swivel

3. 

##  Common Problems

###  The following problems may occur when using this framework:

1. **Permission Issues:**
	* **NoneType in Lat or Long values:** The framework may not be able to access certain functionalities due to system restrictions or permissions. In such cases, <code> Settings->Privacy and Security->Location Services->Python->[Enable]</code>

```python
2024-11-18 14:13:07,002 - INFO - Requesting 'Always' authorization for location services.
2024-11-18 14:13:07,002 - INFO - Location services are enabled.
2024-11-18 14:13:07,003 - INFO - Authorization not determined.
2024-11-18 14:13:17,038 - WARNING - Timeout exceeded while waiting for location.
2024-11-18 14:14:13,177 - INFO - Requesting 'Always' authorization for location services.
2024-11-18 14:14:13,177 - INFO - Location services are enabled.
2024-11-18 14:14:13,178 - INFO - Location services authorized (Always).
2024-11-18 14:14:13,781 - INFO - Location updated: Latitude = 36.062653316751934, Longitude = -115.09186781691349


```



## Getting Started
To get started with the SWIVEL Framework

1. Git clone https://github.com/blakdayz/swivel/framework.git
2. Run <code> pip install poetry </code> in terminal
3. Run <code> poetry install </code> in terminal


## Permissions Setup (MacOS Sequoia 15.1)
