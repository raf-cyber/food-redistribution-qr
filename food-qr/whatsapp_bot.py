import os
from twilio.twiml.messaging_response import MessagingResponse
from register import register_user
from dotenv import load_dotenv

load_dotenv()

# In-memory conversation state
# Format: { phone_number: { 'step': 'name'|'dependents', 'name': str } }
sessions = {}


def handle_message(incoming_msg, from_number):
    response = MessagingResponse()
    msg = response.message()

    # Clean the phone number — remove whatsapp: prefix
    phone = from_number.replace('whatsapp:', '')
    incoming = incoming_msg.strip()

    # Get or create session
    session = sessions.get(phone, {})
    step = session.get('step', 'start')

    if step == 'start':
        sessions[phone] = {'step': 'name'}
        msg.body(
            "Assalam o Alaikum! Welcome to the Community Food Network.\n\n"
            "To register, I need two things from you.\n\n"
            "First — what is your full name?"
        )

    elif step == 'name':
        sessions[phone] = {
            'step': 'dependents',
            'name': incoming
        }
        msg.body(
            f"Thank you, {incoming}.\n\n"
            "How many children or dependents under 18 are in your household?\n\n"
            "Reply with a number. For example: 0, 1, 2, 3"
        )

    elif step == 'dependents':
        if not incoming.isdigit():
            msg.body("Please reply with a number only. For example: 2")
            return str(response)

        name = session.get('name')
        dependents = int(incoming)

        # Register the user
        user_id = register_user(name, phone, dependents)

        if user_id is None:
            # Already registered
            msg.body(
                "This number is already registered in our system.\n\n"
                "If you need help or have lost your QR code, "
                "please contact the NGO directly."
            )
            sessions.pop(phone, None)
            return str(response)

        # Send confirmation with QR link
        qr_url = f"http://localhost:5000/scan?user_id={user_id}"

        msg.body(
            f"You are registered, {name}!\n\n"
            f"Your daily allocation: based on your family size.\n\n"
            f"Your personal QR code link:\n{qr_url}\n\n"
            f"Save this message. Open this link at any participating "
            f"store before closing time to collect your meal.\n\n"
            f"JazakAllah Khair."
        )

        # Clear session
        sessions.pop(phone, None)

    else:
        # Unknown state — reset
        sessions.pop(phone, None)
        msg.body(
            "Sorry, something went wrong. "
            "Please send any message to start again."
        )

    return str(response)