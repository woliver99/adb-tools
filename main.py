import subprocess
from time import sleep
from TerminalMenu import *

ADB_PATH = os.path.abspath("./adb")
SCRCPY_PATH = os.path.abspath("./scrcpy/scrcpy.exe")

GLOBAL_SCRCPY_ARGS = [
    "--video-bit-rate=8M",
]
SCRCPY_PRESETS: dict[str, list[str]] = {
    "Default": [],
    "Quest 2": [
        "--crop=1600:900:2017:510",
        "--no-control",
    ],
}


# ----------------------------------------------------------
# ADB Commands
# ----------------------------------------------------------


def adb_devices() -> str:
    return subprocess.check_output(["adb", "devices"], start_new_session=True).decode("utf-8").removesuffix("\n")


def get_device_ip(device_id: str) -> str | None:
    # Try getting the IP via 'getprop' first
    try:
        ip_prop = (
            subprocess.check_output(
                ["adb", "-s", device_id, "shell",
                    "getprop", "dhcp.wlan0.ipaddress"]
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

    menu = OptionMenu(menu_title, options, exit_runnable)
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

    port = int(NumberInput(
        "Enter port number",
        default_value=5555,
        exit_runnable=lambda: exit(0),
        min_value=1024,
        max_value=65535
    ).prompt())

    # Get the device IP
    device_ip = get_device_ip(device_id)
    if not device_ip:
        print("Could not retrieve IP. Check your device’s Wi-Fi interface name.")
        return

    # Enable wireless ADB on that port
    subprocess.run(["adb", "-s", device_id, "tcpip", str(port)], check=True)

    # Disconnect stale connections for this IP:port and connect wirelessly
    subprocess.run(["adb", "disconnect", f"{device_ip}:{port}"])
    subprocess.run(["adb", "connect", f"{device_ip}:{port}"])


def remove_offline_connections():
    devices = adb_devices_list("\toffline")

    if len(devices) == 0:
        print("No offline connections found.")
        return

    for device in devices:
        disconnect_single_device(device)

    print("All offline connections removed.")


def disconnect_devices():
    """
    Allows disconnecting from all devices at once or selecting an individual device to disconnect.
    """

    options = [
        Option("Wireless devices", disconnect_all_devices),
        Option("Offline devices", remove_offline_connections),
    ]

    devices = adb_devices_list()
    for device in devices:
        options.append(
            Option(f"Device: {device}", lambda d=device: disconnect_single_device(d)))

    def exit_runnable():
        print("Exiting disconnect menu without action.")
        return

    callable = OptionMenu("Disconnect Menu", options, exit_runnable).prompt()
    print("\n")
    callable()


def launch_scrcpy():
    device_id = select_device_id("Select a device to mirror with scrcpy")
    if not device_id:
        return

    args: list[str] = []

    max_fps = int(NumberInput(
        "Enter max fps",
        default_value=60,
        exit_runnable=lambda: exit(0),
        min_value=1,
        max_value=None
    ).prompt())
    args.append(f"--max-fps={max_fps}")

    print("\n")

    options = [
        Option("Enable audio capture (disables audio on the headset)", lambda: None),
        Option("Disable audio capture", lambda: args.append("--no-audio")),
    ]
    OptionMenu("Audio capture",
               options, default_index=2).prompt()()

    print("\n")

    options: list[Option] = []
    for preset in SCRCPY_PRESETS:
        options.append(
            Option(preset, lambda p=preset: args.extend(SCRCPY_PRESETS[p])))
    OptionMenu("Select a preset", options, default_index=1).prompt()()

    # Add global args
    args.extend(GLOBAL_SCRCPY_ARGS)

    cmd = [SCRCPY_PATH, "-s", device_id]
    cmd.extend(args)
    subprocess.run(cmd)

# ----------------------------------------------------------
# Main function
# ----------------------------------------------------------


def main():
    # Change to ADB directory
    os.chdir(ADB_PATH)

    clear_terminal()
    print("Welcome to ADB tools!")
    print()

    # Show current ADB devices
    print(adb_devices())

    # Define menu options
    options = [
        Option("Enable wireless connection to a device", connect_wirelessly),
        Option("Disconnect device(s)", disconnect_devices),
        Option("Launch scrcpy on a device", launch_scrcpy)
    ]

    callable = OptionMenu("ADB Menu", options).prompt()
    print("\n")
    callable()

    print("\n\nLoading ADB devices...")
    sleep(2)
    print(adb_devices())


if __name__ == "__main__":
    main()
