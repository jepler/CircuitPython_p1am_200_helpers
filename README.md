# p1am_200_helpers

Helpers to simplify initialization of features and shields for the P1AM-200.

## Usage

Below are some examples of helper functions. See the helpers_example.py file for a complete example.

```python
import p1am_200_helpers as helper

led = helper.get_led() # get the yellow LED
led.value = True # turn on the LED

eth = helper.get_ethernet() # get the ethernet object and automatically use built-in MAC address
print(f"IP Address is: {eth.pretty_ip(eth.ip_address)}") # print IP address

rtc = helper.get_rtc() # get the real time clock object
helper.sync_rtc(-5) # sync RTC with NTP server, offset by -5 hours for EST
print(rtc_format_time(rtc)) # print current time

# etc.
```

