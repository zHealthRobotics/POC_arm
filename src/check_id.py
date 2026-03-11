import serial
import time

PORT = "/dev/ttyACM0"   # change if needed
BAUD = 1000000

ser = serial.Serial(PORT, BAUD, timeout=0.02)

def checksum(data):
    return (~sum(data)) & 0xFF

def ping(servo_id):
    pkt = [0xFF,0xFF,servo_id,2,0x01]  # header, id, len, ping
    pkt.append(checksum(pkt[2:]))
    
    ser.write(bytes(pkt))
    time.sleep(0.005)
    
    resp = ser.read(6)
    return len(resp) >= 6

print("Scanning IDs...")

found = []
for i in range(0, 253):
    if ping(i):
        print(f"Found servo at ID {i}")
        found.append(i)

if not found:
    print("No servo found")

