from getpass import getpass
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED, ZipFile


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "dist"
OUTPUT_FILE = OUTPUT_DIR / "pico2w-circuitpython.zip"
APP_FILES = ("code.py", "sensors.py", "index.html")
LIB_DIR = PROJECT_DIR / "lib"


def main():
    ssid = input("Wi-Fi network name: ").strip()
    if not ssid:
        raise SystemExit("Wi-Fi network name cannot be empty.")

    if sys.stdin.isatty():
        password = getpass("Wi-Fi password (hidden): ")
    else:
        password = input("Wi-Fi password: ")
    secrets_content = "secrets = %r\n" % {"ssid": ssid, "password": password}

    missing_files = [name for name in APP_FILES if not (PROJECT_DIR / name).is_file()]
    if missing_files:
        raise SystemExit("Missing project file(s): " + ", ".join(missing_files))

    OUTPUT_DIR.mkdir(exist_ok=True)
    with ZipFile(OUTPUT_FILE, "w", ZIP_DEFLATED) as bundle:
        for name in APP_FILES:
            bundle.write(PROJECT_DIR / name, arcname=name)
        if LIB_DIR.is_dir():
            for library_file in sorted(LIB_DIR.rglob("*")):
                if library_file.is_file():
                    bundle.write(library_file, arcname=library_file.relative_to(PROJECT_DIR))
        bundle.writestr("secrets.py", secrets_content)

    print("Created:", OUTPUT_FILE)
    print("The ZIP contains your Wi-Fi password. Keep it private.")
    print("Extract its files to the root of the board's CIRCUITPY drive.")


if __name__ == "__main__":
    main()