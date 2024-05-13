"""
	Example: NTP RTC Helper

    This example demonstrates the use of the NTP_RTC helper class in ntp_rtc_helper.py
    This class is designed to make it easier to sync the P1AM-200 RTC with an NTP server.

	 _____  _____
	|  P  ||  S  |
	|  1  ||  L  |
	|  A  ||  O  |
	|  M  ||  T  |
	|  -  ||     |
	|  2  ||  0  |
	|  0  ||  1  |
	|  0  ||     |
	 ¯¯¯¯¯  ¯¯¯¯¯
	Written by FACTS Engineering
	Copyright (c) 2023 FACTS Engineering, LLC
	Licensed under the MIT license.

"""

from p1am_200_helpers import get_rtc, get_ethernet, sync_rtc, pretty_print_time

# RTC / ETH
rtc = get_rtc()
eth = get_ethernet() # DHCP is enabled by default
print("My IP address is:", eth.pretty_ip(eth.ip_address))

# NTP Settings
timezone_offset = -5    # Time zone offset in hours (EST is -5)
sync_interval = 1       # Next sync in minute(s)
next_sync = rtc.datetime.tm_min


while True:
    if rtc.datetime.tm_min == next_sync or rtc.datetime_compromised:
        print("Syncing with NTP server...")
        sync_rtc(timezone_offset)       # Sync the RTC with the NTP server
        pretty_print_time()
        next_sync = (rtc.datetime.tm_min + sync_interval) % 60
