# MONITOR IP CHANGES

import subprocess
from main import *

# Data obtained from main.py
file_data = data["update_ip.py"]
last_ip = data["update_ip.py"]["last_ip"]
ip_poll_status = int(data["update_ip.py"]["ip_poll_status"])

# Return tuple with (function state, ip)
def check_ip():
    # Check with three different providers
    ip1 = subprocess.run(['curl', '-s', 'https://ipinfo.io/ip'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    ip2 = subprocess.run(['wget', '-qO-', 'https://ipecho.net/plain'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    ip3 = ""
    try:
        ip3 = subprocess.run(['curl', '-s', 'checkip.dyndns.org'], stdout=subprocess.PIPE).stdout.decode('utf-8').split(" ")[5].split("<")[0]
    except IndexError:
        ip3 = ""

    # If all match
    if ip1 == ip2 == ip3:
        return (0, ip3)
    # If only two match, return the faulty number
    elif ip1 == ip2:
        return (3, ip2)
    elif ip1 == ip3:
        return (2, ip3)
    elif ip2 == ip3:
        return (1, ip3)
    # If none match, return all
    else:
        return [4, ip1, ip2, ip3]

# RUN

ip = check_ip()
message = []

# New unnotified issue or correction
if ip_poll_status != ip[0]:
    if ip[0] == 0:
        message.append("The IP provider issue has been resolved")
    elif ip[0] == 4:
        message.append("None out of 3 IP providers match, below is their output")
        message.append(ip[1])
        message.append(ip[2])
        message.append(ip[3])
    else:
        message.append("Warning: IP provider " + str(ip[0]) + " might be failing.")
    # Update status
    data["update_ip.py"]["ip_poll_status"] = str(ip[0])
    save_changes_to_config()

# If the state is 4 (none match), make ip[1] the most probable
if ip[0] == 4:
    import re
    ip_regex = re.compile('[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}')
    if ip_regex.fullmatch(ip[2]):
        ip[1] = ip[2]
    elif ip_regex.fullmatch(ip[3]):
        ip[1] = ip[3]
    # If issue is new
    if ip_poll_status != 4:
        message.append("The most probable IP is: " + ip[1])

# IP has changed since last checked
if last_ip != str(ip[1]):
    message.append("New IP:")
    message.append(ip[1])
    data["update_ip.py"]["last_ip"] = str(ip[1])
    save_changes_to_config()

send_message(message)
