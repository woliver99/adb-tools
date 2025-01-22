import subprocess
import platform
from time import sleep
from TerminalMenu import *

bin_path = os.path.abspath(f"./resources/{platform.system().lower()}")
ADB_PATH = f"{bin_path}/adb"
SCRCPY_PATH = f"{bin_path}/scrcpy/scrcpy.exe"

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


def enable_wireless(device_id: str, port: int) -> bool:
    subprocess.run(["adb", "-s", device_id, "tcpip", str(port)], check=True)
    return True


def connect_wireless(ip: str, port: int) -> bool:
    subprocess.run(["adb", "connect", f"{ip}:{port}"], check=True)
    return True


def launch_scrcpy(device_id: str, extra_args: list[str]):
    print(SCRCPY_PATH)
    cmd = [SCRCPY_PATH, "-s", device_id]
    cmd.extend(extra_args)
    subprocess.run(cmd)


def stop_server():
    print("Killing ADB server...")
    subprocess.run(["adb", "kill-server"])

# ----------------------------------------------------------
# Tools
# ----------------------------------------------------------


def spacer():
    print("\n")


def exit_message(reason: str = "") -> None:
    spacer()
    exit_message = "Returning to menu"

    # If there is a reason, add it
    if reason.strip() != "":
        exit_message = f"{reason}. {exit_message}"

    print(exit_message)


def adb_devices_list(text_to_search: str = "\tdevice") -> list[str]:
    result = adb_devices().splitlines()
    devices: list[str] = []
    for line in result:
        if text_to_search in line:
            devices.append(line.split()[0])
    return devices


def valid_adb_device() -> bool:
    devices = adb_devices_list()
    try:
        while len(devices) == 0:
            print(
                "No connected ADB devices detected. Please connect a device and try again.")
            input("Press Enter to scan for devices again.")
        return True
    except (KeyboardInterrupt):
        exit_message()
        return False


def select_device_id(menu_title: str = "Select an ADB device") -> str | None:
    if not valid_adb_device():
        exit_message("No ADB devices found")
        return None

    devices = adb_devices_list()

    # Wrap each device in an Option that returns the device ID when called
    options: list[Option] = []
    for dev in devices:
        options.append(Option(dev, lambda d=dev: d))

    menu = OptionMenu(menu_title, options, exit_message)
    callable = menu.prompt()
    device_id: str = callable()
    return device_id


def remove_offline_connections():
    devices = adb_devices_list("\toffline")

    if len(devices) == 0:
        print("No offline connections found.")
        return

    for device in devices:
        disconnect_single_device(device)

    print("All offline connections removed.")


# ----------------------------------------------------------
# Actions
# ----------------------------------------------------------


def menu_wireless():
    device_id = select_device_id()
    if device_id is None:
        return

    spacer()

    response = NumberInput(
        "Enter port number",
        default_value=5555,
        exit_runnable=exit_message,
        min_value=1024,
        max_value=65535
    ).prompt()
    if response is None:
        return

    port = int(response)

    # Get the device IP
    device_ip = get_device_ip(device_id)
    if not device_ip:
        print("Could not retrieve IP. exiting.")
        return

    spacer()

    enable_wireless(device_id, port)
    # Disconnect stale connections for this IP:port and connect wirelessly
    disconnect_single_device(f"{device_ip}:{port}")
    connect_wireless(device_ip, port)
    sleep(2)


def menu_disconnect():
    options = [
        Option("Wireless devices", lambda: (
            spacer(), disconnect_all_devices())),
        Option("Offline devices", lambda: (
            spacer(), remove_offline_connections())),
    ]

    if not valid_adb_device():
        print("No ADB devices found. Exiting the menu.")
        return
    devices = adb_devices_list()
    for device in devices:
        options.append(
            Option(f"Device: {device}", lambda d=device: (spacer(), disconnect_single_device(d))))

    OptionMenu("Disconnect Menu", options, exit_message).prompt()()


def menu_scrcpy():
    device_id = select_device_id("Select a device to mirror with scrcpy")
    if not device_id:
        return

    spacer()

    args: list[str] = []

    max_fps = NumberInput(
        "Enter max fps",
        default_value=60,
        exit_runnable=exit_message,
        min_value=1,
        max_value=None
    ).prompt()
    if max_fps is None:
        return
    args.append(f"--max-fps={int(max_fps)}")

    spacer()

    options = [
        Option("Enable audio capture (disables audio on the headset)", lambda: True),
        Option("Disable audio capture", lambda: False),
    ]
    response = OptionMenu("Audio capture",
                          options, default_index=2,
                          exit_runnable=exit_message).prompt()()
    if response == None:
        return
    elif response == False:
        args.append("--no-audio")

    spacer()

    options: list[Option] = []
    for preset in SCRCPY_PRESETS:
        options.append(
            Option(preset, lambda p=preset: (args.extend(SCRCPY_PRESETS[p]), True)[1]))
    response = OptionMenu("Select a preset", options,
                          default_index=1, exit_runnable=exit_message).prompt()()
    if response == None:
        return

    # Add global args
    args.extend(GLOBAL_SCRCPY_ARGS)
    clear_terminal()
    launch_scrcpy(device_id, args)
    input("\n\nPress Enter to return to the menu")


# ----------------------------------------------------------
# Main function
# ----------------------------------------------------------


def main():
    # Change to ADB directory
    os.chdir(ADB_PATH)

    while True:
        clear_terminal()
        print("Welcome to ADB tools!\n")
        print(adb_devices())

        # Define menu options
        options = [
            Option("Enable wireless connection to a device", menu_wireless),
            Option("Disconnect device(s)", menu_disconnect),
            Option("Launch scrcpy on a device", menu_scrcpy),
            Option("Refresh devices", lambda: print("\033[1A\033[1A\033[1A")),
            Option("Kill adb server", lambda: (
                stop_server(), spacer(), exit(0))),
        ]

        callable = OptionMenu("ADB Menu", options,
                              exit_runnable=lambda: (print("Goodbye!"), spacer(), exit(0))).prompt()

        spacer()

        callable()

        spacer()
        print("Loading ADB devices...")
        sleep(1)


if __name__ == "__main__":
    main()
