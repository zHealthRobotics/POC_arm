import serial
import time

PORT = "/dev/ttyACM0"
BAUD = 1000000

ser = serial.Serial(PORT, BAUD, timeout=0.1)

def checksum(data):
    return (~sum(data)) & 0xFF

def write_pos_ex(servo_id, pos, speed, acc):
    pos_l = pos & 0xFF
    pos_h = (pos >> 8) & 0xFF
    spd_l = speed & 0xFF
    spd_h = (speed >> 8) & 0xFF

    params = [
        41,          # WRITE_POS_EX
        acc,
        pos_l, pos_h,
        0, 0,        # time (unused)
        spd_l, spd_h
    ]

    length = len(params) + 2
    packet = [0xFF, 0xFF, servo_id, length, 0x03] + params
    packet.append(checksum(packet[2:]))

    ser.write(bytes(packet))


# -------- Example usage --------
write_pos_ex(servo_id=1, pos=2047, speed=1500, acc=50)
write_pos_ex(servo_id=2, pos=2047, speed=1200, acc=30)
write_pos_ex(servo_id=3, pos=2047, speed=1200, acc=30)
write_pos_ex(servo_id=4, pos=2047, speed=1200, acc=30)
write_pos_ex(servo_id=5, pos=2047, speed=1200, acc=30)
write_pos_ex(servo_id=6, pos=2047, speed=1200, acc=30)
write_pos_ex(servo_id=7, pos=2047, speed=1200, acc=30)

print("Done")

