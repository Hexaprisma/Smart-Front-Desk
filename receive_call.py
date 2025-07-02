import os
from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather

app = Flask(__name__)
@app.route("/receive_call", methods=['GET', 'POST'])
def receive_call():
    """
    Function to receive a call and respond with a message.
    """
    # Create a new TwiML response
    response = VoiceResponse()
    gather = Gather(input='speech', timeout=10)
    gather.say("Welcome to the AI phone operator. How can I assist you today?")
    response.append(gather)
    return Response(str(response), mimetype='text/xml')

@app.route("/handle_speech", methods=['GET', 'POST'])
def handle_speech():
    """
    Function to handle the speech input from the user.
    """
    # Get the speech input from the request
    speech_input = request.values.get('SpeechResult', '')
    
    # Process the speech input (this is where you would integrate with your AI model)
    response_text = f"You said: {speech_input}. How can I help you further?"
    
    # Convert the response text to speech
    return text_to_speech(response_text)

def text_to_speech(text):
    """
    Function to convert text to speech.
    """
    response = VoiceResponse()
    response.say(text)
    return Response(str(response), mimetype='text/xml')

if __name__ == "__main__":
    app.run(debug=True)

    """
    # Get the port from environment variable or default to 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='127.0.0.1', port=port)
    """
    