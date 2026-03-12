# Windows Setup Guide (WSL + Docker + ROS2)

This guide explains how to run the **POC_arm ROS2 workspace** on **Windows using Docker and WSL**.

---

# 1. Clone the Repository

Install Git if not already installed, then clone the repository.

```bash
git clone https://github.com/zHealthRobotics/POC_arm.git
```

---

# 2. Install Docker Desktop

Download and install Docker Desktop:

[https://docs.docker.com/desktop/setup/install/windows-install/](https://docs.docker.com/desktop/setup/install/windows-install/)

During installation:

* Keep **all default settings**
* Restart your computer when prompted
* Launch Docker Desktop
* Sign in or create a Docker account

Wait until the bottom-left of Docker Desktop shows: Engine running

---

# 3. Install WSL

Open **PowerShell as Administrator** and run:

```powershell
wsl --install
```

Then update WSL:

```powershell
wsl --update
```

---

# 4. Install Ubuntu in WSL

In **PowerShell (Administrator)** run:

```powershell
wsl --install -d Ubuntu
```

When prompted:
Create a Unix username (example: office)
Create a password

---

# 5. Enable Docker Integration with WSL

Open **Docker Desktop**.

Go to:

Settings → Resources → WSL Integration

Enable toggle named Ubuntu

Click: Apply & Restart

---

# 6. Give Docker Permission in Ubuntu

Open the **Ubuntu terminal** and run:

```bash
sudo usermod -aG docker $USER
```

Restart WSL(In PowerShell):

```powershell
wsl --shutdown
```

Then open Ubuntu again using: wsl

---

# 7. Install VSCode and Dev Containers Extension

Install **Visual Studio Code** if not already installed.

Install the extension:

```
Dev Containers
```

Now open the **POC_arm folder** in VSCode.

---

# 8. Install USB Passthrough Tool

Open **PowerShell as Administrator** and install usbipd:

```powershell
winget install usbipd
```

Verify installation:

```powershell
usbipd --version
```

---

# 9. Attach the USB Device to WSL

Connect the **USB-C cable** to your device.

List connected USB devices:

```powershell
usbipd list
```

Example output:

USB-Enhanced-SERIAL CH343 (COM5)
BUSID: 2-3
Remember the **BUSID**.

Bind the device:

```powershell
usbipd bind --busid 2-3
```

Attach the device to WSL:

```powershell
usbipd attach --wsl --busid 2-3
```

Verify attachment:

```powershell
usbipd list
```

---

# 10. Verify Serial Device in WSL

Open the Ubuntu terminal:

```powershell
wsl
```

Check available serial ports:

```bash
ls /dev/tty*
```

or

```bash
ls /dev/ttyACM*
```

You should see something like:
/dev/ttyACM0
or
/dev/ttyUSB0

---

# 11. Enable Device in Docker

Open:

```
docker-compose.yml
```

Uncomment the **devices section** and set the correct serial device.

Example:

```
devices:
  - /dev/ttyACM0:/dev/ttyACM0
```

---

# 12. Rebuild the Dev Container

In **VSCode** press:

```
Ctrl + Shift + P
```

Run:

```
Dev Containers: Rebuild and Reopen Container
```

After the container starts, open a terminal and verify the device:

```bash
ls -l /dev/ttyACM*
```

---

# 13. Build the ROS2 Workspace

Inside the container terminal:

```bash
colcon build
```

Then source the workspace:

```bash
source install/setup.bash
```

---

# 14. Set Servo ID

Run:

```bash
ros2 run waveshare_servos set_id --ros-args -p start_id:=1 -p new_id:=2
```

---

# 15. Check Servo ID

Navigate to the source directory:

```bash
cd src
```

Run:

```bash
python3 check_id.py
```

---

# 16. Set All Servo Positions to Zero

```bash
cd src
python3 servo.py
```

---
