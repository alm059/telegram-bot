from configparser import ConfigParser
import requests

data = ConfigParser(comment_prefixes='/', allow_no_value=True)
data.read('data.ini')

def send_message(message_array, user=data["main"]["admin"]):
    headers = {'ContentType': 'multipart/form-data'}
    request_body = {'chat_id': user}
    for message in message_array:
        # Check for aditional payload to send in the message, such as reply
        if type(message) is dict:
            request_body["text"] = message["text"]
        else:
            request_body["text"] = message
        requests.post("https://api.telegram.org/bot" + data["main"]["bot_token"] + "/sendMessage", data=request_body, headers=headers)

# Obtain first unread message from valid users
# When called again will return next unread message
# If returns None, no unread messages
def get_message():
    # Request to check for new messages
    parameters = {'offset': data["main"]["current_offset"]}
    try:
        request = requests.get("https://api.telegram.org/bot" + data["main"]["bot_token"] + "/getUpdates", params=parameters)
        # No new messages
        if request.json()["result"] == []:
            return

        # Increase offset so message is deleted from server on next request
        data["main"]["current_offset"] = str(int(data["main"]["current_offset"]) + 1)
        save_changes_to_config()

        # Get message and its payload (message_id, from, chat, date and text)
        try:
            message = request.json()["result"][0]["message"]
        except KeyError:
            if "edited_message" in request.json()["result"][0].keys():
                send_message(["Edited messages are unsupported"])
            return

        # Check message comes from a valid user
        if str(message["from"]["id"]) not in data["main"]["valid_users"].split(", "):
            # Report to admin
            send_message(["Unknown message sender: ", message])
            # Ignore message and reread
            return get_messages()

        return message
    except requests.exceptions.HTTPError as errh:
        send_message([errh])
    except requests.exceptions.ConnectionError as errc:
        send_message([errc])
    except requests.exceptions.Timeout as errt:
        send_message([errt])
    except requests.exceptions.RequestException as err:
        send_message([err])
    return

def save_changes_to_config():
    with open('data.ini', 'w') as data_file:
        data.write(data_file)
