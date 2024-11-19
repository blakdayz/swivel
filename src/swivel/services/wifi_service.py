import logging
import subprocess
import re
from typing import Tuple, List, Any

from events.event_subsystem import EventBus


class WiFiNetwork:
    """
    Represents a WiFi network with its associated properties.
    """

    def __init__(
        self,
        ssid: str,
        channel: int,
        security: str,
        signal: int,
        noise: int,
        phy_mode: str,
        network_type: str,
    ):
        self.ssid = ssid
        self.channel = channel
        self.security = security
        self.signal = signal
        self.noise = noise
        self.phy_mode = phy_mode
        self.network_type = network_type

    def __str__(self):
        return (
            f"SSID: {self.ssid}, Channel: {self.channel}, Security: {self.security}, "
            f"Signal: {self.signal} dBm, Noise: {self.noise} dBm"
        )


class WiFiInterface:
    """
    Represents a WiFi Interface with attributes for its name, MAC address,
    supported channels, current network, and other available networks.
    """

    def __init__(
        self,
        name: str,
        mac_address: str = None,
        supported_channels: str = None,
        current_network: WiFiNetwork = None,
        other_networks: list[WiFiNetwork] = None,
    ):
        self.name = name
        self.mac_address = mac_address
        self.supported_channels = supported_channels
        self.current_network = current_network
        self.other_networks = other_networks or []

    def add_network(self, network: WiFiNetwork):
        self.other_networks.append(network)

    def __str__(self):
        interface_str = f"Interface: {self.name}, MAC: {self.mac_address}, Supported Channels: {self.supported_channels}\n"
        if self.current_network:
            interface_str += f"Current Network: {self.current_network}\n"
        if self.other_networks:
            interface_str += "Other Networks:\n"
            for network in self.other_networks:
                interface_str += f"  {network}\n"
        return interface_str


class WifiSubscriber:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.event_bus.subscribe_wifi_networks_updated(
            self.on_wifi_networks_updated
        )

    def on_wifi_networks_updated(self, wifi_networks_data):
        # Handle the WiFi networks data update
        print(f"Received WiFi networks update: {wifi_networks_data}")

    def unsubscribe(self):
        self.event_bus.unsubscribe(
            "wifi_networks_updated", self.on_wifi_networks_updated
        )


class WiFiScanner:
    """
    WiFiScanner class scans and parses Wi-Fi information from the system_profiler command on macOS.
    Methods:
    - __init__: Initializes a new instance of the WiFiScanner class.
    - scan: Executes the system_profiler command to fetch Wi-Fi details and parses the output.
    - parse_output: Parses the output obtained from the system_profiler command to extract Wi-Fi information.
    - display_interfaces: Displays parsed Wi-Fi interfaces and their respective details.
    """

    def __init__(self):
        self.interfaces = []

    def scan(self):
        try:
            result = subprocess.run(
                ["system_profiler", "SPAirPortDataType"],
                stdout=subprocess.PIPE,
            )
            output = result.stdout.decode("utf-8")
            self.parse_output(output)
        except subprocess.SubprocessError as e:
            logging.error(f"Error running subprocess: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")

    def parse_network(self, lines, idx):
        network = WiFiNetwork(
            ssid=None,
            channel=None,
            security=None,
            signal=None,
            noise=None,
            phy_mode=None,
            network_type=None,
        )
        while idx < len(lines) and not lines[idx].startswith("PHY Mode"):
            line = lines[idx]
            if "SSID" in line:
                network.ssid = line.split(": ")[1] or "Hidden SSID"
            if "Channel" in line:
                network.channel = int(line.split(": ")[1])
            if "Security" in line:
                network.security = line.split(": ")[1]
            if "Signal" in line:
                signal_noise = re.findall(r"(-?\d+) dBm", line)
                if signal_noise:
                    network.signal = int(signal_noise[0])
                    network.noise = (
                        int(signal_noise[1]) if len(signal_noise) > 1 else None
                    )
            idx += 1
        return network

    def parse_output(self, output):
        current_interface = None
        lines = output.splitlines()
        for idx, line in enumerate(lines):
            line = line.strip()
            if line.startswith("Interfaces:"):
                current_interface = None
            if line.startswith("en0:") or line.startswith("awdl0:"):
                if current_interface:
                    self.interfaces.append(current_interface)
                name = line.split(":")[0]
                current_interface = WiFiInterface(name=name)
            if "MAC Address" in line and current_interface:
                current_interface.mac_address = line.split(": ")[1]
            if "Supported Channels" in line and current_interface:
                current_interface.supported_channels = line.split(": ")[1]
            if current_interface and "Current Network Information" in line:
                current_interface.current_network = self.parse_network(
                    lines, idx
                )
            if current_interface and "Other Local Wi-Fi Networks:" in line:
                while idx < len(lines):
                    network = self.parse_network(lines, idx)
                    current_interface.add_network(network)
                    idx += 1
        if current_interface:
            self.interfaces.append(current_interface)

    def display_interfaces(self):
        for interface in self.interfaces:
            print(interface)

    def get_wifi_networks_data(self) -> Any:
        """
        Returns the WifiNetwork Objectt
        :return:
        """
        return self.interfaces


if __name__ == "__main__":
    wifi_scanner = WiFiScanner()
    wifi_scanner.scan()
    wifi_scanner.display_interfaces()
