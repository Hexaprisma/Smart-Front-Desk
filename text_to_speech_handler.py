import pyttsx3

class TextToSpeechHandler:
    """
    A class to handle text-to-speech conversion using pyttsx3.
    """
    
    def __init__(self):
        self.engine = pyttsx3.init()
    
    def speak(self, text):
        """
        Converts text to speech and plays it.
        
        :param text: The text to be converted to speech.
        """
        self.engine.say(text)
        self.engine.runAndWait()

# This code initializes a text-to-speech engine and converts a sample text to speech.
# It uses the pyttsx3 library, which is a text-to-speech conversion library in Python.
# The `text_to_speech_handler` function takes a string input and uses the engine to speak it aloud.
# The `if __name__ == "__main__":` block is used to test the function with a sample text when the script is run directly.
# Make sure to install the pyttsx3 library using `pip install pyttsx3` before running this code.
