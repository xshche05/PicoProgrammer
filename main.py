from machine import Pin
import time


def sleep_ns(ns):
    time.sleep(ns / 1e9)


def sleep_ms(ms):
    time.sleep_ms(ms)


def slepp_us(us):
    time.sleep_us(us)

d = [i for i in range(64)]

class ShiftRegister:

    def __init__(self, ser, oe, rclk, srclk, srclr, len=8):
        self.ser = Pin(ser, Pin.OUT, value=0)
        self.oe = Pin(oe, Pin.OUT, value=1)
        self.rclk = Pin(rclk, Pin.OUT, value=0)
        self.srclk = Pin(srclk, Pin.OUT, value=0)
        self.srclr = Pin(srclr, Pin.OUT, value=1)
        self.len = len

    def clear(self):
        self.srclr.value(0)
        self.srclr.value(1)

    def shift(self):
        self.srclk.value(1)
        self.srclk.value(0)

    def latch(self):
        self.rclk.value(1)
        self.rclk.value(0)

    def on(self):
        self.oe.value(0)

    def off(self):
        self.oe.value(1)

    def send_bit(self, bit):
        self.ser.value(bit)
        self.shift()

    def send_byte(self, data: int):
        bits = [int(b) for b in f"{data:08b}"]
        bits = bits[::-1]
        for bit in bits:
            self.send_bit(bit)
        self.latch()


class EEPROM:

    def __init__(self, sr, io_pins, ce, oe, we):
        self.sr = sr
        self.sr.on()
        self.io_pins = [Pin(pin, Pin.OUT) for pin in io_pins]
        self.ce = Pin(ce, Pin.OUT, value=1)
        self.oe = Pin(oe, Pin.OUT, value=1)
        self.we = Pin(we, Pin.OUT, value=1)

    def set_1(self):
        self.ce.value(1)
        self.oe.value(1)
        self.we.value(1)

    def set_0(self):
        self.ce.value(0)
        self.oe.value(0)
        self.we.value(0)

    def io_output(self):
        for pin in self.io_pins:
            pin.init(Pin.OUT)

    def io_input(self):
        for pin in self.io_pins:
            pin.init(Pin.IN)

    def set_address(self, address):
        address = [int(b) for b in f"{address:024b}"]
        #address = address[::-1]
        #print(address)
        self.sr.clear()
        for bit in address:
            self.sr.send_bit(bit)
        self.sr.latch()

    def read_byte(self, address):
        self.io_input()
        self.set_address(address)

        self.ce.value(0)
        self.oe.value(0)

        sleep_ns(150)

        byte = 0

        # # 7 pin is least significant bit
        # for i, pin in enumerate(self.io_pins[::-1]):
        #     byte |= pin.value() << i

        # 7 pin is most significant bit
        for i, pin in enumerate(self.io_pins):
            byte |= pin.value() << i

        self.set_1()

        return byte

    def read_page(self, page, page_size):
        page = page * page_size
        return [self.read_byte(page + i) for i in range(page_size)]

    def write_bytes(self, addresses, data):
        self.io_output()
        self.oe.value(0)
        sleep_ms(50)
        self.oe.value(1)
        for address, byte in zip(addresses, data):
            self.set_address(address)
            self.ce.value(1)
            self.we.value(1)
            sleep_ns(150)

            # # 7 pin is least significant bit
            # for i, pin in enumerate(self.io_pins[::-1]):
            #     pin.value((byte >> i) & 1)

            # 7 pin is most significant bit
            for i, pin in enumerate(self.io_pins):
                pin.value((byte >> i) & 1)

            sleep_ns(100)
            self.ce.value(0)
            self.we.value(0)
        self.set_1()
        sleep_ns(150)

    def enable_protection_AT29C010A(self):
        adrs = [0x5555, 0x2AAA, 0x5555]
        data = [0xAA, 0x55, 0xA0]
        self.write_bytes(adrs, data)
        sleep_ms(10)

    def disable_protection_AT29C010A(self):
        adrs = [0x5555, 0x2AAA, 0x5555, 0x5555, 0x2AAA, 0x5555]
        data = [0xAA, 0x55, 0x80, 0xAA, 0x55, 0x20]
        self.write_bytes(adrs, data)
        sleep_ms(10)

    def erase_chip_AT29C010A(self):
        adrs = [0x5555, 0x2AAA, 0x5555, 0x5555, 0x2AAA, 0x5555]
        data = [0xAA, 0x55, 0x80, 0xAA, 0x55, 0x10]
        self.write_bytes(adrs, data)
        sleep_ms(10)

    # def enable_protection_AT28C64(self):
    #     adrs = [0x1555, 0x0AAA, 0x1555]
    #     data = [0xAA, 0x55, 0xA0]
    #     self.write_bytes(adrs, data)
    #
    # def disable_protection_AT28C64(self):
    #     adrs = [0x1555, 0x0AAA, 0x1555, 0x1555, 0x0AAA, 0x1555]
    #     data = [0xAA, 0x55, 0x80, 0xAA, 0x55, 0x20]
    #     self.write_bytes(adrs, data)


sr = ShiftRegister(ser=5, oe=6, rclk=7, srclk=8, srclr=9)

eeprom = EEPROM(sr=sr, io_pins=[10, 11, 12, 13, 14, 15, 16, 17], we=18, oe=19, ce=20)
