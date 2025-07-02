from speech_to_text_handler import SpeechToTextHandler
from openai_project import OpenAIProject
from text_to_speech_handler import TextToSpeechHandler


def on_program_awake():
    global openai_message, console_message, s2t_handler, t2s_handler, project
    
    console_message = "Console Log: "
    print(f"{console_message} initializing openai platform")
    project = OpenAIProject()
    print(f"{console_message} OpenAI platform initialized successfully")

    print(f"{console_message} initializing speech to text handler")
    s2t_handler = SpeechToTextHandler()
    print(f"{console_message} speech to text handler initialized successfully")
    print(f"{console_message} initializing text to speech handler")
    t2s_handler = TextToSpeechHandler()
    print(f"{console_message} text to speech handler initialized successfully")
    openai_message = project.printMessage()
    t2s_handler.speak(openai_message)

def state_machine():
    on_program_awake()
    while True:
        print(f"{console_message} program is listening for audio input...")
        capture_message = listen()
        if capture_message == 1:
            print(f"{console_message} No audio input detected, retrying...")
            continue
        elif capture_message == "exit":
            print(f"{console_message} Exiting program as per user request.")
            break
        print(f"{console_message} program received message: {capture_message}")
        openai_message = project.start_conversation(str(capture_message))
        print(f"{console_message} OpenAI response: {openai_message}")
        t2s_handler.speak(openai_message)


def speak(text):
    """
    Converts text to speech using the text_to_speech_handler.
    :param text: The text to be converted to speech.
    """
    t2s_handler.speak(text)

def listen():
    """
    Listens for audio input and converts it to text using the transcribe_audio function.
    :return: The transcribed text from the audio input.
    """
    # write a function try to listen to audio, time out after 10 seconds
    try:
        return s2t_handler.listen_to_vosk()
    except TimeoutError:
        print(f"{console_message} Listening timed out.")
        return 1

if __name__ == "__main__":
    try:
        state_machine()
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Exiting program.")
    
