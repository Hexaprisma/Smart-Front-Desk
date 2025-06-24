from openai import OpenAI
import sqlite3
import json
from tenacity import retry, wait_random_exponential, stop_after_attempt
from SqlManager import SqlManager
from CalendarHelper import calendar_manager

sqlManager = SqlManager

#now replaced with the calendar manager method
#conn = sqlite3.connect("data/shopData/TestingData.db")
calendar = calendar_manager.CalendarManager()
conn = calendar.conn
print("Opened database successfully")


#SQLite methods

#this is the actual program I/O for OpenAI to visit database
def ask_database(conn, query):
    """Function to query SQLite database with a provided SQL query."""
    try:
        results = str(conn.execute(query).fetchall())
    except Exception as e:
        results = f"query failed with error: (e)"
    return results


database_schema_dict = calendar.get_database_info()
database_schema_string = "\n".join(
    [
        f"Table: {table['table_name']}\nColumns:{', '.join(table['column_names'])}"
        for table in database_schema_dict
    ]
)

def registerSchedule(time,date,specialistID):
    cursor = conn.cursor()
    cursor.execute('''
    SELECT "{date}"
    FROM Shop_Schedule
    WHERE time_slot = ?
    AND ("{date}" IS NULL OR "{date}" = '');
    INSERT INTO Shop_Schedule (Time_Slots, "{date}")
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, phone, 'confirm', date, time, service, specialistID, notes))

    # Commit the transaction to save the changes
    conn.commit()

    # Close the connection
    conn.close()
def registerCustomer(name, phone, date, time, service, specialistID, notes = 'None'):
    cursor = conn.cursor()
    # Insert data into the 'customerInfo' table
    cursor.execute('''
    INSERT INTO customerInfo (Name, PhoneNumber, State, ReservedDate,ReservedTime, Services, PerferedSpecialistID, Notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, phone, 'confirm', date, time, service, specialistID, notes))

    # Commit the transaction to save the changes
    conn.commit()

    # Close the connection
    conn.close()

    print("Your reservation has been complete.")


#We dont check specialist at this point, since we only have one specialist table
def check_calendar(date, time, specialist=None):
    output = calendar.check_appointment_availability(date, time, specialist)
    return output
    

#func that will return the next solution
def make_reservation(user_name = None, phoneNumber = None, date = None, time = None, service = None, specialist = "Any"):
    """Function to make reservation for user by accessing SQLite database."""
    print("user name: " + user_name, "phone number: " + phoneNumber, "date: " + date, "time: " + time, "service: " + service, "specialist: " + specialist)
    if((user_name == None) or (phoneNumber == None) or (date == None) or (service == None)):
        return ("Ask the user to provide all missing information.")
    
    returnCode = calendar.add_appointment(user_name, phoneNumber, date, time, service, specialist)
    if(returnCode == 0):
        return ("Tell the user the reservation has been complete, ask if more help is needed.")
    elif(returnCode == 1):
        return ("Service is not offered by the shop, ask for clarify.")
    elif(returnCode == 2):
        return ("Outside business hours, ask the user to choose another time, or tell the user what time is avaliable.")
    elif(returnCode == 3):
        return ("All specialists are booked, ask for another time or wait.")
    else:
        return ("Tell the user that an unexpected error occured, visit shop website to see more details.")

def cancel_reservation(name, phoneNumber, time, date):
    """Function to cancel reservation for user, must verify phoneNumber in order to process"""
    if(sqlManager.cancelSchedule(date, time, phoneNumber)):
        print(f"Your reservation at {date} {time} has been canceled!")
    else:
        print(f"Cancelation aborted!")

aiTools = [
    {
        "type": "function",
        "function": {
            "name": "ask_database",
            "description": "Use this function to answer user questions about shop info. Input should be a fully formed SQL query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": f"""
                                SQL query extracting info to answer the user's question.
                                SQL should be written using this database schema:
                                {database_schema_string}
                                The query should be returned in plain text, not in JSON.
                                """,
                    }
                },
                "required": ["query"],
            },
        }
    },

    {
        "type": "function",
        "function": {
            "name": "check_calendar",
            "description": "Use this function to check the shop calendar and availability.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": f"""
                                User proposed date, use this for checking whether the shop is open.
                                date should be written using this format:
                                {"year-month-date"}
                                The date should be returned in plain text, not in JSON.
                                """,
                    },
                    "time": {
                        "type": "string",
                        "description": f"""
                                User proposed time, use this for checking the time whether the reservation is available.
                                time should be written using this format in 24 hours:
                                {"10:30"}
                                The time should be returned in plain text, not in JSON.
                                """,
                    },
                    "specialist": {
                        "type": "string",
                        "description": f"""
                                User preferred specialist, not a required input, only pass in when user is asking for.
                                The specialist should be returned in plain text, not in JSON.
                                """,
                    }
                },
                "required": ["date, time, specialist=None"],
            },
        }
    },

    {
        "type": "function",
        "function": {
            "name": "make_reservation",
            "description": "collect all necessary information from the user. If any of these is missing, ask the user to privode it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_name": {
                        "type": "string",
                        "description": "The first name user provided.",
                    },
                    "date": {
                        "type": "string",
                        "description": "The weekday user want to reserve, from Monday to Sunday.",
                    },
                    "time": {
                        "type": "string",
                        "description": "The time period when the user wish to reserve.",
                    },
                    "service": {
                        "type": "string",
                        "description": "The name of the service that the user wish to order, only options avaliable from ask_database."
                    },
                    "phoneNumber": {
                        "type": "string",
                        "description": "The phone number user provided."
                    },
                    "specialist":{
                        "type": "string",
                        "description": "The specific specialist user wish to have, this is optional."
                    }
                },
                "required": ["user_name", "date", "time", "service","phoneNumber"]
            },
        }
    },

]

#open ai events

client = OpenAI()
GPT_MODEL = "gpt-3.5-turbo"

messages = [
    {"role":"system",
    "content": "Your name is Lynx and you are a shop assistant, skilled in customer services. You should get the customer's first and last name, phone number, and services they want."},
    {"role": "system", "content": "Your response should be as comscise as possible, don't use complex language."},
    {"role": "system", "content": "Don't make assumptions about what customers want. Ask for clarification if a user request is ambiguous."},
    {"role": "system", "content": "Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous."},
    {"role": "system","content":"only use database information to answer questions. Do not speak anything unrelated to database information."},
    {"role":"user","content":"You are working for Herbal Nail Bar now, start by greeting to user"}
    ]



#This Print message is for call without tools
def printMessage():
    model_response_with_function_call = client.chat.completions.create(
    model = GPT_MODEL,
    messages=messages,
)
    print("printMessage log: ", model_response_with_function_call.choices[0].message.content)

#print the first message:
printMessage()

#try the function for 3 times before declare failure
@retry(wait = wait_random_exponential(multiplier = 1, max = 40), stop = stop_after_attempt(3))
def chat_completion_request(tools = None, tool_choice="auto", model=GPT_MODEL):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )
        print("chat_completion_request: ", response.choices[0].message.content)
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Execption: {e}")
        return e
    

def ResponseManager(response_message):
    #print(response_message.tool_calls[0])
    tool_calls = response_message.tool_calls
    if tool_calls:
        #if true the model will return the name of the tool / 
        # function ot call and the arugment(s)
        tool_call_id = tool_calls[0].id
        tool_function_name = tool_calls[0].function.name
        #we might need to set another condition to check if tool_calls valid for 
        if tool_function_name == 'make_reservation':
            userName = json.loads(tool_calls[0].function.arguments)['user_name']
            userPN = json.loads(tool_calls[0].function.arguments)['phoneNumber']
            scheduleTime = json.loads(tool_calls[0].function.arguments)['time']
            scheduleDate = json.loads(tool_calls[0].function.arguments)['date']
            scheduleService = json.loads(tool_calls[0].function.arguments)['service']
            scheduleSpecialist = json.loads(tool_calls[0].function.arguments).get('specialist', "Any")
            
            results = make_reservation(userName, userPN, scheduleTime, scheduleDate, scheduleService, scheduleSpecialist)
            #print result
            
            messages.append({
                "role":"tool",
                "tool_call_id":tool_call_id,
                "name":tool_function_name,
                "content":results
            })

            printMessage()

        elif tool_function_name == 'ask_database':
            tool_query_string = json.loads(tool_calls[0].function.arguments)['query']
            results = ask_database(conn, tool_query_string)

            messages.append({
                "role":"tool",
                "tool_call_id":tool_call_id,
                "name": tool_function_name,
                "content": results
            })

            # Invoke the chat completion API with the function response
            # appended to the messages list.
            # Messages with role 'tool' must be a response to a preceding message 
            # with 'tool_calls'.
            printMessage()
        elif tool_function_name == 'check_calendar':
            date = json.loads(tool_calls[0].function.arguments)['date']
            time = json.loads(tool_calls[0].function.arguments)['time']
            specialist = json.loads(tool_calls[0].function.arguments)['specialist']            
            results = check_calendar(date, time, specialist)
        else:
            print(f"Error: function {tool_function_name} does not exist")
    else:
        #model did not identify a function to call, result can be returned to the user
        print(response_message.content)


#user input section
while True:
    user_input = input("Enter something (or type 'exit' to quit): ")
    if user_input.lower() == 'exit':
        print("Exiting the conversation.")
        break
    else:
        messages.append({"role":"user","content": user_input})
        response = chat_completion_request(tools = aiTools, model=GPT_MODEL)
        #print conversation result
        response_message = response.choices[0].message
        #print(response_message)
        messages.append(response_message)
        #check if tool is used:
        ResponseManager(response_message)
        


