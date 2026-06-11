import subprocess
import webbrowser
import os
import sys
import shutil
import time

def install_adb():
    """Detects OS and installs ADB if missing."""
    print("[*] ADB not found. Attempting automatic installation...")
    
    try:
        if sys.platform == "linux":
            # Works for Debian/Ubuntu/Mint
            print("[*] Detected Linux. Running: sudo apt-get update && sudo apt-get install -y android-tools-adb")
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "android-tools-adb"], check=True)
            
        elif sys.platform == "darwin":
            # Requires Homebrew on macOS
            if not shutil.which("brew"):
                print("[-] Error: Homebrew is required to auto-install ADB on Mac. Install it at brew.sh")
                return False
            print("[*] Detected macOS. Running: brew install --cask android-platform-tools")
            subprocess.run(["brew", "install", "--cask", "android-platform-tools"], check=True)
            
        elif sys.platform == "win32":
            # Downloads standalone tools for Windows
            print("[*] Detected Windows. Downloading Platform Tools from Google...")
            import requests, zipfile
            url = "https://google.com"
            r = requests.get(url)
            with open("adb_tools.zip", "wb") as f: f.write(r.content)
            with zipfile.ZipFile("adb_tools.zip", "r") as zip_ref: zip_ref.extractall(".")
            # Add to local PATH for this session
            os.environ["PATH"] += os.pathsep + os.path.abspath("platform-tools")
            print("[+] Windows ADB ready in local folder.")
            
        return True
    except Exception as e:
        print(f"[-] Auto-installation failed: {e}")
        return False

def run_adb(command):
    """Utility to run ADB commands via system subprocess."""
    try:
        full_cmd = ["adb"] + command.split()
        return subprocess.check_output(full_cmd, stderr=subprocess.STDOUT).decode('utf-8').strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def run_fastboot(command):
    """Utility to run ADB commands via system subprocess."""
    try:
        full_cmd = ["fastboot"] + command.split()
        return subprocess.check_output(full_cmd, stderr=subprocess.STDOUT).decode('utf-8').strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def setup_pixel_flow():
    print("--- PIXEL PREPARATION FLOW ---")
    
    # 1. Developer Options
    print("\n[STEP 1: DEVELOPER OPTIONS]")
    input("1. Open 'Settings' on your Pixel. (Press Enter when done)")
    input("2. Scroll down and tap 'About phone'. (Press Enter when done)")
    input("3. Tap 'Build number' 7 times until it says 'You are now a developer'. (Press Enter when done)")
    
    # 2. USB Debugging
    print("\n[STEP 2: USB DEBUGGING]")
    input("1. Go back to 'Settings' > 'System' > 'Developer options'. (Press Enter when done)")
    input("2. Scroll down and toggle 'USB Debugging' to ON. (Press Enter when done)")
    print("\n[*] Connect your phone to the PC now.")
    input("3. Look at your phone! Check 'Always allow from this computer' and tap 'Allow'. (Press Enter when done)")

    # Verification Loop for ADB
    print("\n[*] Verifying ADB connection...")
    while True:
        # Using the run_adb function from earlier
        status = run_adb("get-state")
        if status == "device":
            print("[+] Connection verified!")
            break
        else:
            input("[-] Device not detected. Ensure 'Allow' was tapped on the screen. Press Enter to retry...")

    # 3. OEM Unlocking
    print("\n[STEP 3: OEM UNLOCKING]")
    input("1. In 'Developer options', find 'OEM unlocking' and toggle it ON. (Press Enter when done)")
    
    # Final Verification
    oem_status = run_adb("shell getprop ro.oem_unlock_supported")
    if oem_status == "1":
        print("[+] OEM Unlocking is now ready!")
    else:
        print("[!] Warning: OEM Unlocking might still be disabled on your device.")

    print("\n--- SETUP COMPLETE ---")
    print("Your Pixel is now ready for bootloader unlocking and rooting.")

setup_pixel_flow()
def needs_boot_img():
    """
    Returns:
        True: if the device uses boot.img (launched on Android 12 or older).
        False: if the device uses init_boot.img (launched on Android 13 or newer).
    """
    try:
        # Get the API level the phone originally shipped with
        cmd = ["adb", "shell", "getprop ro.product.first_api_level"]
        first_api = subprocess.check_output(cmd).decode('utf-8').strip()
        
        # If the property is empty, check the current version as a fallback
        if not first_api:
            cmd_fallback = ["adb", "shell", "getprop ro.build.version.sdk"]
            first_api = subprocess.check_output(cmd_fallback).decode('utf-8').strip()

        api_level = int(first_api)

        # API 33 is Android 13. 
        # Devices launching with 13+ use init_boot.
        if api_level >= 33:
            print(f"[*] API {api_level} detected. Use init_boot.img.")
            return False
        else:
            print(f"[*] API {api_level} detected. Use boot.img.")
            return True

    except Exception as e:
        print(f"[-] Error detecting boot type: {e}")
        # Default to True (boot.img) as it's the legacy standard
        return True
if needs_boot_img():
    needsboot = True
else:
    needsboot = False
time.sleep(1)

input("Your device will factory reset. Press enter to continue.")
time.sleep(1)
run_adb("reboot bootloader")
print("Please wait 30 seconds...")
time.sleep(30)
input("Your bootloader will get unlocked and your device will factory reset. Press enter to continue.")
if needsboot == False:
    fastboot_run("flashing unlock")
if needsboot == True:
    fastboot_run("oem unlock")
input("Confirm on your phone. (press enter to continue)")
print("Resetting.")
print("Please wait 30 seconds.")
time.sleep(30)
input("Finish your phone setup. Press enter to continue.")
input("Have you really finished your phone setup? Press enter to confirm.")
time.sleep(6)
setup_pixel_flow()
time.sleep(8)
def get_boot_image():
    # 1. Ensure ADB is installed
    if not shutil.which("adb"):
        # If it's not in the system PATH, check the local folder too
        local_adb = "./platform-tools/adb" if sys.platform != "win32" else "platform-tools/adb.exe"
        
        if not os.path.exists(local_adb):
            if not install_adb():
                print("[-] Please install ADB manually and try again.")
                return

    print("[*] Waiting for device... Please ensure USB Debugging is ON.")
    
    # 2. Wait for a connected device
    while True:
        devices = run_adb("devices")
        if devices and "device" in devices.split('\n')[1:]:
            break
        time.sleep(2)
    on_pixel = input("Are you on a Google Pixel? Write 'Y' if you are and 'N' if you are not.")
    if on_pixel == "N"
        print("Get your boot image or device firmware. Automatic boot image finder supports only Pixel devices. (press enter to continue)")
        input()
        return "nah user is not on a pixel"

    # 3. Detect Model and Build
    codename = run_adb("shell getprop ro.product.device")
    build_id = run_adb("shell getprop ro.build.display.id")

    if not codename or not build_id:
        print("[-] Error: Could not read device properties.")
        return

    print(f"\n[+] Success! Device: {codename.upper()}")
    print(f"[+] Exact Build: {build_id}")
    
    # 4. Redirect to the exact section
    target_url = f"https://google.com{codename}"
    print(f"[*] Redirecting to: {target_url}")
    print(f"[!] Press Ctrl+F and search for '{build_id}'. Then download.")
    
    webbrowser.open(target_url)

time.sleep(1)
get_boot_image()
input("Press enter when you have downloaded your boot image.")
input("Extract the zip file with your boot image. Press enter when you have extracted.")
time.sleep(3.5)



if needs_boot_img() == True:
    print("Find the file boot.img from your extracted zip and")
    oem = True
else:
    print("Find the file init_boot.img from your extracted zip and")
    oem = False
imgpath = input("enter the file path here: ").replace('"', '').replace("'", "").strip()

input("Make sure you have entered the right file path. If not, this program will close. Press enter to continue")

print("Transferring the boot image to your phone automatically.")
time.sleep(2.5)
run_adb("push " + imgpath + " /sdcard/Download/")
print("Done")
print()
time.sleep(0.4)
print("Installing the magisk app to your phone.")
time.sleep(1.2)

run_adb("install magisk.apk")
time.sleep(8)
print("Done")
print()

time.sleep(2.5)
input("Open the Magisk app on your phone. Press enter when done.")
input('Press "Install" or "Install Magisk" inside the Magisk app. Press enter when done.')
input('Press "Select and patch a file" inside the Magisk app. Press enter when done.')
input('Choose the boot image that the computer installed to your phone. Press enter when done.')
input('Press "Lets go" in the Magisk app. Press enter when done.')
print("Please wait...")
sleep(7.5)
print("Magisk has patched your boot image.")
print("Wait...")
sleep(5)
def pull_magisk_image():
    print("[*] Searching for patched image on phone...")
    # Find the filename
    filename = run_adb("shell ls /sdcard/Download/magisk_patched_*.img")
    
    if filename and "magisk_patched" in filename:
        print(f"[+] Found: {filename}")
        # Pull and rename
        run_adb(f"pull /sdcard/Download/{filename} magiskboot.img")
        print("[+] Success! Saved as 'magiskboot.img' on your PC.")
        return True
    else:
        print("[-] Error: No patched image found in /sdcard/Download/")
        return False

if pull_magisk_image():
    print("Rebooting to bootloader...")
    adb_run("reboot bootloader")
    print("Please wait 60 seconds.")
    time.sleep(60)
    print("Flashing boot image")
    if oem == True:
        run_fastboot("flash boot magiskboot.img")
    if oem == False:
        run_fastboot("flash init_boot magiskboot.img")
    print("Please wait 15 seconds...")
    time.sleep(15)
    print("Rebooting...")
    time.sleep(1)
    run_fastboot("reboot")
    time.sleep(5)
    print("Your phone is successfully rooted. Press enter to exit.")
    input()
else:
    print("No boot image patched or found. Press enter to exit.")
    input()






