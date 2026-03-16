# Windows Setup Guide (WSL + Docker + ROS2)

This guide explains how to run the **POC_arm ROS2 workspace** on **Windows using Docker and WSL**.

---

# 1. Install Docker Desktop

Download and install Docker Desktop:

[https://docs.docker.com/desktop/setup/install/windows-install/](https://docs.docker.com/desktop/setup/install/windows-install/)

During installation:

* Keep **all default settings**
* Restart your computer when prompted
* Launch Docker Desktop
* Sign in or create a Docker account

Wait until the bottom-left of Docker Desktop shows **Engine running**.

---

# 2. Install WSL

Open **PowerShell as Administrator** and run:

```powershell
wsl --install
```

Then update WSL:

```powershell
wsl --update
```

---

# 3. Install Ubuntu in WSL

In **PowerShell (Administrator)** run:

```powershell
wsl --install -d Ubuntu
```

When prompted:

Create a Unix username (example: `office`)
Create a password (example: `0`)

---

# 4. Enable Docker Integration with WSL

Open **Docker Desktop**

Go to:

Settings → Resources → WSL Integration

Enable the toggle named **Ubuntu**

Click **Apply & Restart**

---

# 5. Give Docker Permission in Ubuntu

Open the **Ubuntu terminal** and run:

```bash
sudo usermod -aG docker $USER
```

Restart WSL from PowerShell:

```powershell
wsl --shutdown
```

Then open Ubuntu again:

```powershell
wsl
```

---

# 6. Clone the Repository in WSL

Inside the **Ubuntu terminal** run:

```bash
git clone https://github.com/zHealthRobotics/POC_arm.git
cd POC_arm
```

---

# 7. Install USB Passthrough Tool

Open **PowerShell as Administrator** and install usbipd:

```powershell
winget install usbipd
```

Verify installation:

```powershell
usbipd --version
```

---

# 8. Attach the USB Device to WSL

Connect the **USB-C cable** to your device.

List connected USB devices:

```powershell
usbipd list
```

Example output may show something like:

```
USB-Enhanced-SERIAL CH343 (COM5)
BUSID: 2-3
```

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

# 9. Verify Serial Device in WSL

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

```
/dev/ttyACM0
```

or

```
/dev/ttyUSB0
```

---

# 10. Verify Device Mapping in Docker

Open the file:

```
docker-compose.yml
```

Verify that the **devices section contains the correct serial device**.

Example:

```
devices:
  - /dev/ttyACM0:/dev/ttyACM0
```

If your device appears as `/dev/ttyUSB0` or another name in WSL, update the mapping accordingly.

Example:

```
devices:
  - /dev/ttyUSB0:/dev/ttyUSB0
```

---

# 11. Start the Docker Container

Inside the repository directory run:

```bash
./start_container.sh
```

This will:

* Build the Docker image
* Start the container
* Enter the ROS2 workspace environment

---

# 12. Build the ROS2 Workspace

Inside the container terminal run:

```bash
colcon build
```

Then source the workspace:

```bash
source install/setup.bash
```

---

# 13. Check Servo ID

```bash
cd src
python3 check_id.py
```

---

# 14. Set Servo ID

```bash
ros2 run waveshare_servos set_id --ros-args -p start_id:=1 -p new_id:=2
```

---

# 15. Set All Servo Positions to Zero

```bash
cd src
python3 servo.py
```
---

# 16. Start the Robot Control System

Inside the **Docker container terminal**, navigate to the ROS2 workspace and ensure it is built and sourced.

First build the workspace:

```bash
colcon build
```

Source the workspace:

```bash
source install/setup.bash
```

Then launch the MoveIt control system:

```bash
ros2 launch poc_v2_moveit moveit_poc.launch.py
```
---
