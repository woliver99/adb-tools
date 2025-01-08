import subprocess
from time import sleep
from TerminalMenu import *

SCRCPY_PATH = "./scrcpy/scrcpy.exe"
SCRCPY_CUSTOM_ARGS: list[str] = [
    "--no-audio",
    "--video-bit-rate=8M",
    "--max-fps=75",
    "--crop=1600:900:2017:510",
    "--no-control",
]

# ----------------------------------------------------------
# ADB Commands
# ----------------------------------------------------------


def adb_devices() -> str:
    return subprocess.check_output(["adb", "devices"]).decode("utf-8").removesuffix("\n")


def get_device_ip(device_id: str) -> str | None:
    # Try getting the IP via 'getprop' first
    try:
        ip_prop = (
            subprocess.check_output(
                ["adb", "-s", device_id, "shell", "getprop", "dhcp.wlan0.ipaddress"]
            )
            .decode("utf-8")
            .strip()
        )
        if ip_prop:
            return ip_prop
    except:
        pass

    # Fallback to 'ip' command
    try:
        ip_output = subprocess.check_output(
            ["adb", "-s", device_id, "shell", "ip",
                "-f", "inet", "addr", "show", "wlan0"]
        ).decode("utf-8").splitlines()
        for line in ip_output:
            line = line.strip()
            if line.startswith("inet "):
                return line.split()[1].split("/")[0]
    except:
        pass

    return None


def disconnect_all_devices():
    subprocess.run(["adb", "disconnect"])


def disconnect_single_device(device_id: str):
    subprocess.run(["adb", "disconnect", device_id])

# ----------------------------------------------------------
# Tools
# ----------------------------------------------------------


def adb_devices_list(text_to_search: str = "\tdevice") -> list[str]:
    result = adb_devices().splitlines()
    devices: list[str] = []
    for line in result:
        if text_to_search in line:
            devices.append(line.split()[0])
    return devices


def select_device_id(menu_title: str = "Select an ADB device") -> str | None:
    devices = adb_devices_list()

    while len(devices) == 0:
        print("No connected ADB devices detected. Please connect a device and try again.")
        input("Press Enter to scan for devices again.")

    # Wrap each device in an Option that returns the device ID when called
    options: list[Option] = []
    for dev in devices:
        options.append(Option(dev, lambda d=dev: d))

    def exit_runnable():
        print("No device selected. Exiting the menu.")
        return None  # If exit is chosen, we return None

    menu = TerminalMenu(menu_title, options, exit_runnable)
    callable = menu.prompt()
    print("\n")
    device_id: str = callable()
    return device_id


def make_sure_there_is_a_valid_adb_device() -> None:
    devices = adb_devices_list()
    while len(devices) == 0:
        print("No connected ADB devices detected. Please connect a device and try again.")
        input("Press Enter to scan for devices again.")


# ----------------------------------------------------------
# Actions
# ----------------------------------------------------------


def connect_wirelessly():
    make_sure_there_is_a_valid_adb_device()

    device_id = select_device_id()
    if device_id is None:
        return

    port = input("Enter port number (leave blank for 5555): ")
    if not port or not port.isdigit():
        port = "5555"

    # Get the device IP
    device_ip = get_device_ip(device_id)
    if not device_ip:
        print("Could not retrieve IP. Check your device’s Wi-Fi interface name.")
        return

    # Enable wireless ADB on that port
    subprocess.run(["adb", "-s", device_id, "tcpip", port], check=True)

    # Disconnect stale connections for this IP:port and connect wirelessly
    subprocess.run(["adb", "disconnect", f"{device_ip}:{port}"])
    subprocess.run(["adb", "connect", f"{device_ip}:{port}"])
    sleep(2)


def remove_offline_connections():
    devices = adb_devices_list("\toffline")

    if len(devices) == 0:
        print("No offline connections found.")
        return

    for device in devices:
        disconnect_single_device(device)

    print("All offline connections removed.")
    sleep(1)


def disconnect_devices():
    """
    Allows disconnecting from all devices at once or selecting an individual device to disconnect.
    """

    options = [
        Option("All wireless devices", disconnect_all_devices),
    ]

    devices = adb_devices_list()
    for device in devices:
        options.append(
            Option(f"{device}", lambda d=device: disconnect_single_device(d)))

    def exit_runnable():
        print("Exiting disconnect menu without action.")
        return None

    callable = TerminalMenu("Disconnect Menu", options, exit_runnable).prompt()
    print("\n")
    callable()
    sleep(1)


def launch_scrcpy():
    device_id = select_device_id("Select a device to mirror with scrcpy")
    if not device_id:
        return

    cmd = [SCRCPY_PATH, "-s", device_id] + SCRCPY_CUSTOM_ARGS
    subprocess.run(cmd)

# ----------------------------------------------------------
# Main function
# ----------------------------------------------------------


def main():
    clear_terminal()
    print("Welcome to ADB tools!")
    print()

    # Show current ADB devices
    print(adb_devices())

    # Define menu options
    options = [
        Option("Enable wireless connection to a device", connect_wirelessly),
        Option("Remove all offline connections", remove_offline_connections),
        Option("Disconnect a device", disconnect_devices),
        Option("Launch scrcpy on a device", launch_scrcpy)
    ]

    callable = TerminalMenu("ADB Menu", options).prompt()
    print("\n")
    callable()

    print()
    print(adb_devices())


if __name__ == "__main__":
    main()
