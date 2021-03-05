import subprocess
from main import *

# Min python version = 3.6, checks for 3 already done in main.py
if sys.version_info.major == 3 and sys.version_info.minor < 6:
    print("At least Python 3.6 required")
    sys.exit()

# Data obtained from main.py
file_data = data["update_ip.py"]
last_ip = data["update_ip.py"]["last_ip"]
ip_poll_status = int(data["update_ip.py"]["ip_poll_status"])
fail_status = int(data["update_ip.py"]["fail_status"])

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
    elif ip1 == ip2 and ip2 != "":
        return (3, ip2)
    elif ip1 == ip3 and ip3 != "":
        return (2, ip3)
    elif ip2 == ip3 and ip3 != "":
        return (1, ip3)
    # If none match, return all
    else:
        return [4, ip1, ip2, ip3]

#######
# RUN #
#######

ip = check_ip()
message = []

# New unnotified issue or correction
if ip_poll_status != ip[0]:
    if fail_status == 0: # Toggle the alert switch. Notify if fails again
        data["update_ip.py"]["fail_status"] = "1"
    elif fail_status == 1: # Notify
        if ip[0] == 0:
            message.append("The IP provider issue has been resolved")
        elif ip[0] == 4:
            message.append("None out of 3 IP providers have matched twice in a row, below is their output")
            message.append("1: " + ip[1])
            message.append("2: " + ip[2])
            message.append("3: " + ip[3])
        else:
            message.append("Warning: IP provider " + str(ip[0]) + " might be failing. It has failed two times now")
        # Update status
        data["update_ip.py"]["ip_poll_status"] = str(ip[0])
        save_changes_to_config()
else:
    # There is no issue so reset the alert switch
    data["update_ip.py"]["fail_status"] = "0"

# If the state is 4 (none match), make ip[1] the most probable
if ip[0] == 4:
    import re
    ip_regex = re.compile('[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}')
    if ip_regex.fullmatch(ip[2]):
        ip[1] = ip[2]
    elif ip_regex.fullmatch(ip[3]):
        ip[1] = ip[3]
    # If issue is new, notify
    if ip_poll_status != 4 and fail_status == 1:
        message.append("The most probable IP is: " + ip[1])

# IP has changed since last checked
if last_ip != str(ip[1]):
    message.append("New IP:")
    message.append(ip[1])
    data["update_ip.py"]["last_ip"] = str(ip[1])
    save_changes_to_config()

send_message(message)
