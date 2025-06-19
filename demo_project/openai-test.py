import json
from openai import OpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored
from tools import tools

GPT_MODEL = "gpt-3.5-turbo"
client = OpenAI()


#completion = client.chat.completions.create(
#  model="gpt-3.5-turbo",
#  messages=[
#    {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
#    {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming."}
#  ]
#)
#print(completion.choices[0].message)

#try the function for 3 times before declare failure
@retry(wait = wait_random_exponential(multiplier = 1, max = 40), stop = stop_after_attempt(3))
def chat_completion_request(messages, tools = None, tool_choice=None, model=GPT_MODEL):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Execption: {e}")
        return e


def pretty_print_conversation(messages):
  role_to_color = {
    "system": "red",
    "user": "green",
    "assistant": "azure",
    "function": "seraphim",   
  }
  for message in messages:
    if message["role"] == "system":
      print(colored(f"system: {message['content']}\n", role_to_color[message["role"]]))
    elif message["role"] == "user":
      print(colored(f"user: {message['content']}\n", role_to_color[message["role"]]))
    elif message["role"] == "assistant":
      print(colored(f"assistant {message['content']}\n", role_to_color[message["role"]]))
    elif message["role"] == "function":
       print(colored(f"function ({message['name']}): {message['content']}\n", role_to_color[message["role"]]))


messages = []
messages.append({"role": "system", "content": "Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous."})
messages.append({"role": "user", "content": "what is the weather going to be like in San Francisco and Glasgow over the next 4 days"})
chat_response = chat_completion_request(
   messages, tools = tools, model=GPT_MODEL
)
assistant_message = chat_response.choices[0].message.tool_calls
messages.append(assistant_message)
#assistant_message
print(assistant_message)

