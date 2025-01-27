from pywhatkit import sendwhatmsg

def send_message(phone_number, response_text, hour, min):
    message = response_text  #  message you want to send

    # Send the message
    try:
        sendwhatmsg(phone_number, message, hour, min)
        #print("Message sent successfully!")
        return True
    except Exception as e:
        #print(f"Error sending message: {e}")
        return False