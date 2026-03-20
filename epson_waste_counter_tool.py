from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


EPSON_VENDOR_ID = 0x04B8
UTILITY_INTERFACE = 2


def project_root() -> Path:
    return Path(__file__).resolve().parent


def vendor_root() -> Path:
    return project_root() / "vendor"


def load_runtime() -> None:
    """Load vendored dependencies before importing pyusb/reinkpy."""
    libusb_dll = vendor_root() / "libusb-1.0.dll"
    if not libusb_dll.exists():
        raise FileNotFoundError(
            f"Missing {libusb_dll}. Put libusb-1.0.dll in the vendor folder."
        )
    os.environ["PATH"] = str(vendor_root()) + os.pathsep + os.environ.get("PATH", "")
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(vendor_root()))
    sys.path.insert(0, str(vendor_root()))


def show_reset_warning_dialog() -> bool:
    """Show a multilingual blocking warning before any reset operation."""
    message = (
        "IMPORTANT / IMPORTANT / IMPORTANTE\n\n"
        "FR: Ne remettez PAS les compteurs a zero si les tampons d'encre usagee n'ont pas ete reellement nettoyes ou remplaces.\n"
        "Faire un reset logiciel sans nettoyage physique peut provoquer des fuites d'encre et endommager l'imprimante.\n\n"
        "EN: Do NOT reset the counters unless the waste ink pads were physically cleaned or replaced.\n"
        "A software-only reset can cause ink leaks and printer damage.\n\n"
        "ES: NO reinicie los contadores si las almohadillas de tinta residual no fueron limpiadas o reemplazadas fisicamente.\n"
        "Un reinicio solo por software puede causar fugas de tinta y danos en la impresora.\n\n"
        "Choose Yes only if the physical maintenance was already completed."
    )
    try:
        import tkinter
        from tkinter import messagebox

        root = tkinter.Tk()
        root.withdraw()
        result = messagebox.askyesno("Waste Pad Maintenance Warning", message)
        root.destroy()
        return bool(result)
    except Exception:
        print(message)
        answer = input("Type YES to continue: ").strip()
        return answer == "YES"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read or reset Epson waste ink counters over USB on Windows."
    )
    parser.add_argument(
        "--serial",
        action="append",
        help="Target a specific printer serial number. Repeat to target multiple printers.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Target all detected Epson printers exposing the utility USB interface.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List detected compatible Epson USB devices and exit.",
    )
    parser.add_argument(
        "--supported-models",
        action="store_true",
        help="List the models known by the vendored reinkpy database and exit.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset waste counters on the selected printer(s).",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Required together with --reset. Confirms that physical waste-pad maintenance was already done.",
    )
    return parser.parse_args()


def discover_devices() -> list[dict[str, object]]:
    """Discover Epson USB devices that expose the Epson utility interface."""
    import usb.backend.libusb1
    import usb.core
    import usb.util

    backend = usb.backend.libusb1.get_backend()
    if backend is None:
        raise RuntimeError("libusb1 backend unavailable")

    devices = usb.core.find(find_all=True, backend=backend, idVendor=EPSON_VENDOR_ID)
    results: list[dict[str, object]] = []
    for dev in devices:
        utility_iface = None
        for cfg in dev:
            for iface in cfg:
                if iface.bInterfaceNumber == UTILITY_INTERFACE:
                    utility_iface = iface
                    break
            if utility_iface:
                break
        if utility_iface is None:
            continue

        try:
            manufacturer = usb.util.get_string(dev, dev.iManufacturer)
        except Exception:
            manufacturer = None
        try:
            product = usb.util.get_string(dev, dev.iProduct)
        except Exception:
            product = None
        try:
            serial = usb.util.get_string(dev, dev.iSerialNumber)
        except Exception:
            serial = None

        results.append(
            {
                "idVendor": dev.idVendor,
                "idProduct": dev.idProduct,
                "serial_number": serial,
                "manufacturer": manufacturer,
                "product": product,
                "interface": UTILITY_INTERFACE,
            }
        )
    return results


def find_targets(all_devices: list[dict[str, object]], requested_serials: list[str] | None, use_all: bool) -> list[dict[str, object]]:
    if use_all:
        return list(all_devices)
    if requested_serials:
        remaining = set(requested_serials)
        matched = [device for device in all_devices if device.get("serial_number") in remaining]
        found = {device.get("serial_number") for device in matched}
        missing = remaining - found
        if missing:
            raise SystemExit(f"Requested serial(s) not detected: {', '.join(sorted(missing))}")
        return matched
    return list(all_devices)


def get_device(device_info: dict[str, object]):
    from reinkpy import Device

    spec = {
        "idVendor": device_info["idVendor"],
        "idProduct": device_info["idProduct"],
        "bClass": None,
        "bInterfaceNumber": UTILITY_INTERFACE,
        "serial_number": device_info.get("serial_number"),
    }
    return Device.from_usb(**spec)


def get_supported_models() -> list[str]:
    from reinkpy.epson import get_db

    return sorted(get_db().keys())


def get_counter_map(epson) -> dict[int, int]:
    counter_map: dict[int, int] = {}
    for pattern in ("waste counter", "platen pad counter"):
        group = epson.spec.get_mem(pattern)
        if group:
            counter_map.update(zip(group["addr"], group["reset"]))
    return dict(sorted(counter_map.items()))


def format_counter_values(values: list[tuple[int, int | None]]) -> str:
    return ", ".join(f"0x{addr:02X}={value}" for addr, value in values)


def describe_device(device_info: dict[str, object], epson) -> None:
    print(f"Serial: {device_info.get('serial_number') or 'unknown'}")
    print(f"USB product: {device_info.get('product') or 'unknown'}")
    print(f"Detected model: {epson.detected_model or 'unknown'}")
    print(f"Configured model: {epson.spec.model or 'unknown'}")


def inspect_device(device_info: dict[str, object]) -> None:
    device = get_device(device_info)
    epson = device.epson
    describe_device(device_info, epson)

    counter_map = get_counter_map(epson)
    if not counter_map:
        print("Waste counter addresses: unavailable for this model in the current reinkpy database.")
        return

    values = epson.read_eeprom(*counter_map.keys())
    print("Waste counter addresses:")
    print(", ".join(f"0x{addr:02X}" for addr in counter_map.keys()))
    print("Current values:")
    print(format_counter_values(values))
    print("Reset target values:")
    print(", ".join(f"0x{addr:02X}={value}" for addr, value in counter_map.items()))


def reset_device(device_info: dict[str, object]) -> None:
    device = get_device(device_info)
    epson = device.epson
    describe_device(device_info, epson)

    counter_map = get_counter_map(epson)
    if not counter_map:
        raise SystemExit("This model has no known waste counter map in the current reinkpy database.")

    if not any(name.startswith("do_reset_All_waste_counters_") for name in dir(epson)):
        raise SystemExit("This model does not expose a supported waste-counter reset operation.")

    if not show_reset_warning_dialog():
        raise SystemExit("Reset cancelled by user.")

    before = epson.read_eeprom(*counter_map.keys())
    result = bool(epson.reset_waste())
    after = epson.read_eeprom(*counter_map.keys())

    print("Before:")
    print(format_counter_values(before))
    print(f"Reset result: {result}")
    print("After:")
    print(format_counter_values(after))


def main() -> int:
    args = parse_args()
    load_runtime()

    if args.supported_models:
        print("Models known by the vendored reinkpy database:")
        for model in get_supported_models():
            print(f"- {model}")
        return 0

    devices = discover_devices()
    if args.list:
        print("Detected Epson USB utility devices:")
        for device in devices:
            serial = device.get("serial_number") or "unknown"
            product = device.get("product") or "unknown"
            print(f"- {serial} | {product}")
        return 0

    targets = find_targets(devices, args.serial, args.all)
    if not targets:
        print("No compatible Epson printer detected on the utility USB interface.")
        return 1

    if args.reset and not args.yes:
        print("--reset requires --yes to confirm physical waste-pad maintenance.")
        return 2

    for index, device_info in enumerate(targets, start=1):
        print("")
        print(f"Printer {index}/{len(targets)}")
        if args.reset:
            reset_device(device_info)
        else:
            inspect_device(device_info)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
