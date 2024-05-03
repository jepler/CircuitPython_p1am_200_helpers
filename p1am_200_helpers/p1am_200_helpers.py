# Written by FACTS Engineering
# Copyright (c) 2023 FACTS Engineering, LLC
# Licensed under the MIT license.
"""
`p1am_200_helpers`
================================================================================

P1AM-200 Helper Library

Provides helper functions to more easily interface with devices 
and shields on a P1AM-200 CPU. 

* Author(s): Adam Cummick, Tristan Warder, Michael Scott
"""

import storage
import board
from digitalio import DigitalInOut
import busio
import AT24MAC_EEPROM
from adafruit_pcf8563.pcf8563 import PCF8563
import neopixel
import adafruit_sdcard
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socketpool as socketpool
from p1am_200_helpers.ntp_rtc_helper import NTP_RTC, NTPException

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/facts-engineering/CircuitPython_p1am_200_helpers.git"

_internal_i2c = busio.I2C(board.ATMAC_SCL, board.ATMAC_SDA) # internal bus
_rtc = None
_eeprom = None
_eth_iface = None
_eth_socket_pool = None
_port_1_control = None
_port_2_control = None
_vfs = None
_sd_spi = None
_sd_cs = None


def get_switch():
    """Returns a digitalio switch"""
    sw = DigitalInOut(board.SWITCH)
    sw.switch_to_input()
    return sw

def get_led():
    """Returns an digitalio LED"""
    led = DigitalInOut(board.LED)
    led.switch_to_output()
    return led

def set_serial_mode(port, mode=485):
    """Set the serial port mode for the P1AM-Serial.
    Port must be 1 or 2 and mode can be RS485 or RS232.
    Returns the associated DE pin when RS485 is selected,
    None when RS232 is selected.
    """
    global _port_1_control, _port_2_control
    port_de = None

    if port == 1:
        if _port_1_control is None:
            _port_1_control = DigitalInOut(board.SERIAL_MODE1)
        port = _port_1_control
        port_de = board.DE1
    elif port == 2:
        if _port_2_control is None:
            _port_2_control = DigitalInOut(board.SERIAL_MODE2)
        port = _port_2_control
        port_de = board.DE2
    else:
        raise ValueError("Port must be 1 or 2")

    if mode == 232:
        port_de = None
    port.switch_to_output("232" in str(mode))
    return port_de

def get_serial(port, *, mode=485, baudrate=115200, settings="8N1", receiver_buffer_size=1024, timeout=0.1):
    """Returns a serial object for the P1AM-Serial.
    Port must be 1 or 2 and mode can be RS485 or RS232.
    """
    
    port_de = set_serial_mode(port, mode)

    assert settings[1] in "NEO", "Parity must be N, E, or O"
    parity_options = {"N": None, "E": busio.UART.Parity.EVEN, "O": busio.UART.Parity.ODD}
    parity = parity_options[settings[1]]

    data_bits = int(settings[0])
    assert data_bits in range(5, 10), "Data bits must be between 5 and 9"
    stop_bits = int(settings[2])
    assert stop_bits in range(1, 3), "Stop bits must be between 1 and 2"


    if port == 1:
        uart = busio.UART(board.TX1, board.RX1, baudrate=baudrate,  bits=data_bits, parity=parity, stop=stop_bits, receiver_buffer_size=receiver_buffer_size, timeout=timeout)
    elif port == 2: 
        uart = busio.UART(board.TX2, board.RX2, baudrate=baudrate,  bits=data_bits, parity=parity, stop=stop_bits, receiver_buffer_size=receiver_buffer_size, timeout=timeout)
    if port_de is not None:
        return uart, port_de
    return uart


def get_eeprom():
    """Returns an AT24MAC EEPROM object"""
    global _eeprom
    if _eeprom is None:
        _eeprom = AT24MAC_EEPROM.AT24MAC(_internal_i2c, 0b100)
    return _eeprom


def get_rtc():
    """Returns an pcf8563 RTC object"""
    global _rtc
    if _rtc is None:
        _rtc = PCF8563(_internal_i2c)
    return _rtc

def mount_sd(drive_name="/sd"):
    """Mounts the SD card at a given path"""
    global _vfs, _sd_spi, _sd_cs

    _sd_spi = busio.SPI(board.SD_SCK, board.SD_MOSI, board.SD_MISO)
    _sd_cs = DigitalInOut(board.SD_CS)
    card = adafruit_sdcard.SDCard(_sd_spi, _sd_cs)
    _vfs = storage.VfsFat(card)
    storage.mount(_vfs, drive_name)

def unmount_sd():
    """Unmounts the SD card"""
    global _vfs

    storage.umount(_vfs)
    _sd_spi.deinit()
    _sd_cs.deinit()
    _vfs = None

def get_neopixel(color=(0, 0, 0)):
    """Returns a neopixel object"""
    pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, pixel_order=neopixel.GRB)
    pixel[0] = color
    return pixel

def get_ethernet(dhcp=True):
    """intilializes the P1AM-ETH and returns a WIZNET5K ethernet object"""
    global _eth_iface
    if _eth_iface is not None:
        return _eth_iface
    
    cs = DigitalInOut(board.D5)
    spi_bus = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    mac = get_eeprom().mac
    _eth_iface = WIZNET5K(spi_bus, cs, is_dhcp=dhcp, mac=bytes(mac))
    return _eth_iface

def get_socketpool():
    global _eth_iface, _eth_socket_pool
    if _eth_iface is None:
        raise RuntimeError("Ethernet interface not initialized")        
    else:
        if _eth_socket_pool is None:
            _eth_socket_pool = socketpool.SocketPool(_eth_iface)
        return _eth_socket_pool

def sync_rtc(timezone_offset=-5, socketpool=None):
    """Syncs the RTC with the NTP server"""
    global _rtc, _eth_iface

    if _eth_iface is None:
        raise RuntimeError("Ethernet interface not initialized")
    
    if _rtc is None:
        _rtc = get_rtc()
    if socketpool is None:
        socketpool = get_socketpool()
    ntp = NTP_RTC(socketpool, _rtc, timezone_offset)
    try:
        ntp.sync()
    except NTPException as e:
        print(e)
        return False
    return True

def pretty_print_time(datetime=None):
        """Convert datetime to human readable time."""
        global _rtc
        if datetime is None:
            if _rtc is None:
                _rtc = get_rtc()
            t = _rtc.datetime
        else:
            t = datetime
        formatted_time = "Date: {}/{}/{}\nTime: {}:{:02}:{:02}".format(
        t.tm_mon, t.tm_mday, t.tm_year,t.tm_hour, t.tm_min, t.tm_sec)
        print(formatted_time)
    
