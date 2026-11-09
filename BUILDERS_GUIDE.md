# Slotcar Laptimer - Builders Guide

A complete guide to building and setting up the Slotcar Laptimer (v1.1.1) for slot car racing on a Raspberry Pi. Works with 2 lanes out of the box and any larger lane count (e.g. 4) by adding one sensor and one GPIO pin per lane.

## Prerequisites

Before you begin, gather the following components:

### Hardware
- **Raspberry Pi** (Pi 3, Pi 4, or Pi Zero 2W recommended) running Raspberry Pi OS Bookworm or newer
- **Carrera Slot Car Set** - Standard straight section for start/finish line
- **1 LM393 Photoelectric Counter Module per lane** (2 for a 2-lane track, 4 for a 4-lane track) - For lap detection on each lane
- **Display Options** (choose one or more):
  - iPad or tablet (WiFi connected)
  - Laptop or desktop computer (WiFi connected)
  - Raspberry Pi 7" touchscreen (optional, for dedicated display)
- **Additional Hardware**:
  - Micro USB power supply for Raspberry Pi (5V, 2.5A minimum)
  - Jumper wires and breadboard for GPIO connections
  - USB keyboard and mouse (for initial setup)
  - HDMI cable (for initial setup with monitor)

### Knowledge
- Basic familiarity with Raspberry Pi
- Basic soldering skills (optional, for permanent wiring)
- Network access for device downloads and installation

---

## Assembly & Installation

### Step 1: Prepare the Carrera Track

1. **Select the Start/Finish Line**
   - Choose a straight section of track that will serve as your finish line
   - Ensure the section is level and has good contact surfaces for the photoelectric sensors

2. **Identify the Sensor Mounting Points**
   - Determine where each lane's photoelectric sensor will be mounted
   - The sensors should be positioned to detect slot car passage reliably
   - All sensors should be at the same track position for simultaneous lap detection

3. **Plan Wiring Path**
   - Identify the path for wiring from sensors to the Raspberry Pi
   - Plan cable routing to avoid interference and damage during racing
   - Consider using cable trays or clips for neat organization

### Step 2: Modify the Carrera Track for Sensors

**WARNING: This involves cutting and modifying your track. Take precautions and work carefully.**

1. **Cut Access Points in Track**
   - Carefully cut small access points in the track bed where sensors will be mounted
   - Use a rotary tool or file to create clean, level surfaces
   - Test fit the sensor modules before making permanent modifications
   
   ![Sensor mounting point preparation](images/01-track-access-points.jpg)
   ![Close-up of access point](images/02-access-point-detail.jpg)

2. **Disconnect Electrical Components**
   - Disconnect the Carrera power supply
   - Desolder or remove the electrical contacts from the track sections
   - Be careful not to damage the track or contact rails
   - Keep the original contacts safe in case you need to revert modifications
   
   ![Electrical components before removal](images/03-electrical-before.jpg)
   ![Removing electrical contacts](images/04-contact-removal.jpg)
   ![Track after electrical removal](images/05-electrical-after.jpg)

3. **Mount Photoelectric Sensors**
   - Insert the LM393 photoelectric modules into the access points
   - Position sensors to detect car passage at each lane
   - Secure sensors with small brackets or epoxy (non-conductive)
   - Ensure both sensors have a clear view of their respective lanes
   - Test alignment before final mounting
   
   ![Sensor mounting in track](images/06-sensor-mounting.jpg)
   ![Mounted sensors side view](images/07-sensor-side-view.jpg)

4. **Wire Sensor Modules**
   - Connect VCC and GND from each module to a common power source
   - Connect signal wires (OUT pins) from each sensor to separate GPIO pins (one per lane)
   - Use shielded or twisted wire to reduce electromagnetic interference
   - Clearly label each wire (Lane 1, Lane 2, ..., GND, VCC)
   
   ![Sensor wiring setup](images/08-sensor-wiring.jpg)
   ![Wiring detail and connections](images/09-wiring-detail.jpg)

---

### Step 3: Install Raspberry Pi OS

1. **Download Raspberry Pi OS**
   - Visit https://www.raspberrypi.com/software/
   - Download the latest Raspberry Pi Imager or OS image
   - For this project, use "Raspberry Pi OS (Full)" or "Lite" edition

2. **Prepare SD Card**
   - Insert a microSD card (16GB or larger recommended)
   - Use Raspberry Pi Imager to write the OS image
   - Advanced options: Configure hostname, enable SSH, set WiFi credentials
   - Safely eject the SD card

3. **Boot the Raspberry Pi**
   - Insert the microSD card into the Raspberry Pi
   - Connect HDMI monitor, USB keyboard, and mouse
   - Connect the power supply
   - Wait for the system to boot (this may take 2-3 minutes on first boot)

4. **Complete Initial Setup**
   - Set locale, timezone, and keyboard layout
   - Create a user with a strong password (the Imager lets you set this)
   - Configure WiFi connection
   - Update the system: `sudo apt update && sudo apt upgrade -y`
   - Reboot: `sudo reboot`

---

### Step 4: Connect Photoelectric Counter Modules

1. **Identify GPIO Pins**
   - Reference: https://pinout.xyz/
   - Default configuration:
     - Lane 1 signal: GPIO 18 (Physical pin 12)
     - Lane 2 signal: GPIO 23 (Physical pin 16)
     - Lane 3 signal (4-lane example): GPIO 24 (Physical pin 18)
     - Lane 4 signal (4-lane example): GPIO 25 (Physical pin 22)
     - Ground: Any GND pin (e.g., Physical pin 14)
     - 3.3V or 5V for sensor power (see sensor specifications)

2. **Connect Power for Sensors**
   - Identify power requirements for your LM393 modules
   - Most operate on 5V DC
   - Connect VCC wires to a 5V source:
     - Option A: Use a separate 5V power supply
     - Option B: Use Raspberry Pi 5V pin (Physical pin 2 or 4)
   - Connect all GND wires together

   **Wiring diagram example:**
   ```
   LM393 Lane 1          LM393 Lane 2          (Lane 3, 4 ... same pattern)
   ├─ VCC ───────┬─────── VCC
   ├─ GND ───────┴─────── GND
   └─ OUT ──────→ GPIO 18 (Physical pin 12)
                          └─ OUT ──────→ GPIO 23 (Physical pin 16)

   Power Source:
   ├─ 5V ──→ VCC rails
   └─ GND ──→ GND rail
   ```

3. **Connect Wires to Raspberry Pi**
   - Use a breadboard or directly solder to GPIO pins
   - Lane 1 OUT → GPIO 18
   - Lane 2 OUT → GPIO 23
   - Lane 3 / 4 OUT → GPIO 24 / 25 (4-lane track)
   - GND from sensors → Any GND pin on Pi
   - Verify connections with multimeter before powering on

4. **Test GPIO Connection**
   - SSH into the Raspberry Pi:
     ```bash
     ssh <user>@raspberrypi.local  # or ssh <user>@<your-pi-ip>
     ```
   - Most LM393 modules have an LED that lights when the beam is interrupted; use it to check each sensor
   - Full end-to-end test comes in Step 7 (cars crossing the line register laps)

---

### Step 5: Clone and Configure the Project

1. **Clone the Repository**
   ```bash
   cd ~
   git clone https://github.com/berny-pe/slotcar-laptimer.git
   cd slotcar-laptimer
   ```

2. **Verify Python Runtime**
   ```bash
   python3 --version  # Python 3.10 or higher (the code uses `float | None` type syntax)
   pip3 --version     # Should be installed
   ```

3. **Install Python Dependencies**

   GPIO uses `rpi-lgpio`, a drop-in `RPi.GPIO` replacement. The old `RPi.GPIO` package fails with "Failed to add edge detection" on current Raspberry Pi OS. `rpi-lgpio` compiles a C extension, so install the build tools first:
   ```bash
   sudo apt update
   sudo apt install -y swig python3-dev python3-venv liblgpio-dev
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
   The build takes a minute or two. Without `swig` the install fails with "command 'swig' failed".

4. **Configure GPIO Pins** (if different from defaults)
   - The lane count is the number of entries in `LANE_PINS` in `lap_timer/config.py`:
     ```python
     # 2-lane track
     LANE_PINS = [18, 23]
     # 4-lane track
     #LANE_PINS = [18, 23, 24, 25]
     ```
   - Or override without editing code, using BCM pin numbers in lane order:
     ```bash
     SLOT_LANE_PINS="18,23,24,25" python SlotcarLapTimer.py
     ```
   - Pins must be unique. `MIN_LAP_SECONDS` in `config.py` (default 1.0) ignores repeated triggers on the same lane within that time; keep it well below your fastest lap.

5. **Test Python Environment**
   ```bash
   python3 -c "import flask; import RPi.GPIO as GPIO; print('Dependencies OK')"
   ```
   (`rpi-lgpio` provides the `RPi.GPIO` module.)

---

### Step 6: Run the Application

1. **Start the Lap Timer Application**
   ```bash
   # From the repository directory, venv active
   python SlotcarLapTimer.py
   ```
   
   Expected output:
   ```
   * Serving Flask app 'SlotcarLapTimer'
   * Running on http://0.0.0.0:5000
   ```

2. **Keep Server Running**
   - The application will run in the foreground
   - To run in background, use:
     ```bash
     nohup .venv/bin/python SlotcarLapTimer.py > lap_timer.log 2>&1 &
     ```
   
   Or use a process manager like systemd or supervisor

---

### Step 7: Access the Web Interface

1. **Find Your Raspberry Pi's IP Address**
   ```bash
   hostname -I
   ```
   Example output: `192.168.1.42`

2. **Open in Web Browser**
   - **iPad**: Safari → `http://192.168.1.42:5000`
   - **Laptop**: Chrome/Firefox → `http://192.168.1.42:5000`
   - **Raspberry Pi Display**: Firefox → `http://localhost:5000`

3. **Set Up a Race**
   - The first screen is the race setup. Choose one:
     - **Number of laps**: first to finish the target laps wins
     - **Race time**: most laps within the time limit wins; ties go to the car that crossed the line first. After time is up each car finishes its current lap.
   - On a track with more than 2 lanes, tick the lanes that take part (e.g. a 2-car race on a 4-lane track). Unselected lanes are hidden and ignored.
   - Press "Go to race".

4. **Verify the Race Screen**
   - Total time (and lap goal or remaining time) at the top
   - One panel per participating lane: Current lap, Last lap, Fastest lap, Laps count
   - Controls: Start Timer, Continue Timer, Stop Timer, one Lap button per lane (manual trigger for testing), Refresh, Reset

5. **Test Before Racing**
   - Click "Start Timer" (five start lights count down, then the clock starts)
   - Click the "Lap N" buttons, or push a car over each sensor
   - Verify times update, then let the race finish and check the winner message
   - "Reset" asks for confirmation and returns to the setup screen

---

## Racing Tips

1. **Calibrate Sensors**
   - Position cars on track before starting
   - Run test races to ensure sensors detect lap crossings reliably
   - Adjust sensor position or sensitivity if needed

2. **iPad Setup for Racing**
   - Place iPad on a stand or holder visible to all racers
   - Ensure WiFi signal is strong and stable
   - Consider using full-screen mode for better visibility
   - Reduce screen brightness variation with auto-brightness off

3. **Optimal Lighting**
   - Photoelectric sensors work best with consistent lighting
   - Avoid direct sunlight on sensor area
   - Consider adding track lighting for consistent conditions

4. **Network Stability**
   - Restart WiFi if disconnections occur
   - Ensure only intended devices access the lap timer
   - Consider using a dedicated WiFi hotspot for reliability

---

## Troubleshooting

### GPIO Sensor Not Detected
```bash
# Check the sensor LED lights when the beam is blocked
# Verify wiring with multimeter
# Startup error "Failed to add edge detection":
#   - use rpi-lgpio from requirements.txt, not the old RPi.GPIO package
#   - make sure only one instance of the app is running (pins already claimed)
```

### Web Interface Not Accessible
```bash
# Check if Flask is running
ps aux | grep SlotcarLapTimer.py

# Check port 5000 is listening
netstat -tlnp | grep 5000

# Verify firewall allows port 5000
sudo ufw status
sudo ufw allow 5000/tcp
```

### Laps Not Registering
1. Verify sensor power is connected
2. Check GPIO pin configuration matches wiring
3. Test sensors with multimeter during car passage
4. Verify GPIO pin mode (INPUT) is correct
5. Double counts? Raise `MIN_LAP_SECONDS` in `lap_timer/config.py`
6. Laps ignored? Check the lane was selected on the setup screen and `LANE_PINS` order matches the lanes

### Performance Issues
1. Close unnecessary applications
2. Disable screen blanking: `sudo nano /etc/lightdm/lightdm.conf`
3. Reduce browser tabs and extensions
4. Check CPU temperature: `vcgencmd measure_temp`

---

## Next Steps

### Make It Permanent (Optional)

1. **Auto-Start Application**
   - Create systemd service: `/etc/systemd/system/lap-timer.service` running `.venv/bin/python SlotcarLapTimer.py` in the repository folder
   - Enable: `sudo systemctl enable lap-timer.service`
   - Start: `sudo systemctl start lap-timer.service`

2. **Improve Sensor Reliability**
   - Calibrate sensor thresholds (potentiometer on the LM393 module)
   - Tune `MIN_LAP_SECONDS` (built-in debounce)
   - Use better cable shielding

3. **Ideas to Extend**
   - Race history and statistics
   - Sound effects for lap detection

4. **Document Your Build**
   - Take photos of your setup
   - Record sensor specifications and calibration values
   - Keep notes on any modifications

---

## Reference

- **Raspberry Pi**: https://www.raspberrypi.com/
- **GPIO Pinout**: https://pinout.xyz/
- **Flask Documentation**: https://flask.palletsprojects.com/
- **rpi-lgpio Documentation**: https://rpi-lgpio.readthedocs.io/
- **LM393 Datasheet**: Search online for "LM393 comparator datasheet"

---

## Support

For issues or questions:
1. Check the [README.md](README.md) for basic usage
2. Review test cases in [tests/](tests/) for expected behavior
3. Check [ARCHITECTURE.md](ARCHITECTURE.md) for code organization
4. Open an issue on the project repository

Happy racing! 🏁
