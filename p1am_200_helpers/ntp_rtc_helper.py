"""
Helper library for syncing the rtc to a NTP server

Written by FACTS Engineering
Copyright (c) 2023 FACTS Engineering, LLC
Licensed under the MIT license.

"""
import struct
import time

class NTPException(Exception):
    """Exception for NTP errors"""

class NTP_RTC:
    """Helper module to sync the RTC clock with a NTP server for CircuitPython.
    This module does not handle daylight savings.
    :socket: The socket library to use for the NTP client.
    :rtc:               The RTC to sync.
    :time_zone_offset:  The time zone offset in hours.
    :ntp_server:        The NTP server to sync with.
    :retries:           The number of times to retry the NTP request.
    :timeout:           The timeout in seconds to receive the NTP data.
    :debug:             Print debug messages.
    """
    def __init__(
        self,
        socket,
        rtc,
        time_zone_offset,
        *,
        ntp_server="pool.ntp.org",              # Default to pool.ntp.org
        retries=3,                              # Default to 3 retries
        timeout=1,                              # Default to 1 seconds
        debug = False
    ):
        self.socket = socket
        self.rtc = rtc
        self.tz_offset = time_zone_offset * 60 * 60     # Convert to seconds
        self.ntp_server = ntp_server
        self.retries = retries
        self.timeout = timeout
        self._debug = debug


    def sync(self):
        """Sync the RTC with the NTP server."""
        self.set_rtc(self.get_epoch())
    
    def get_epoch(self):
        """Get the current epoch time from the NTP server"""
        time1970 = 2208988800           # Reference time
        recv_data = None
        attempts = 0

        client = self.socket.socket(type=self.socket.SOCK_DGRAM)
        client.settimeout(self.timeout)

        while attempts < self.retries:
            attempts += 1
            try:     
                client.connect((self.ntp_server, 123))     # NTP uses port 123
                client.send(b'\x1b' + 47 * b'\0')
            except Exception as e:
                if self._debug:
                    print(e)
                continue
            
            recv_data = client.recv(128)
            if recv_data:
                epoch_time = struct.unpack("!12I", recv_data)[10]
                client.close()         # Close socket
                return epoch_time - time1970 + self.tz_offset

        client.close()         # Close socket
        raise NTPException("Failed to get NTP time.")

    def set_rtc(self, epoch):
        """Set the RTC time from the epoch time"""

        current_time = time.localtime(epoch)
        formatted_time = time.struct_time((current_time.tm_year, current_time.tm_mon,
                                           current_time.tm_mday, current_time.tm_hour,
                                           current_time.tm_min, current_time.tm_sec,
                                           current_time.tm_wday, -1, -1))
        self.rtc.datetime = formatted_time

    def pretty_print_time(self):
        """Convert datetime to human readable time."""
        t = self.rtc.datetime
        formatted_time = "Date: {}/{}/{}\nTime: {}:{:02}:{:02}".format(
        t.tm_mon, t.tm_mday, t.tm_year,t.tm_hour, t.tm_min, t.tm_sec)
        print(formatted_time)
