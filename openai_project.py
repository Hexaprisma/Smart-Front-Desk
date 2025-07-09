from openai import OpenAI
import sqlite3
import json
from tenacity import retry, wait_random_exponential, stop_after_attempt
from CalendarHelper.calendar_manager import CalendarManager
from datetime import date




class OpenAIProject:
    """OpenAI Project class to handle OpenAI interactions and database queries."""
  
    # Initialize the OpenAIProject with necessary components
    def __init__(self):
        global openAI_log
        openAI_log = "OpenAI Log: "
    
        self.calendar = CalendarManager()
        self.conn = self.calendar.conn
        print(f"{openAI_log} Opened database successfully")
        self.database_schema_dict = self.calendar.get_database_info()
        self.database_schema_string = "\n".join(
            [
                f"Table: {table['table_name']}\nColumns:{', '.join(table['column_names'])}"
                for table in self.database_schema_dict
            ]
        )


        self.aiTools = [
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
                                    {self.database_schema_string}
                                    The query should be returned in plain text, not in JSON.
                                    """,
                        }
                    },
                    "required": ["query"]
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
                    "required": ["date", "time", "specialist"]
                },
            }
        },

        {
            "type": "function",
            "function": {
                "name": "change_reservation",
                "description": "Use this function to change an existing reservation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_name": {
                            "type": "string",
                            "description": """
                                        The customer's full name
                            """,
                        },                        
                        "date": {
                            "type": "string",
                            "description": f"""
                                    User scheduled date, use this for validating the appointment.
                                    date should be written using this format:
                                    {"year-month-date"}
                                    The date should be returned in plain text, not in JSON.
                                    """,
                        },
                        "is_cancel": {
                            "type": "boolean",
                            "description": f"""
                                    Whether the user wants to cancel the appointment.
                                    """,
                        },
                        "time": {
                            "type": "string",
                            "description": f"""
                                    User scheduled time, use this for checking the time whether the reservation is valid.
                                    time should be written using this format in 24 hours:
                                    {"10:30"}
                                    The time should be returned in plain text, not in JSON.
                                    """,
                        },
                        "new_date": {
                            "type": "string",
                            "description": f"""
                                    New date proposed by the user, use this for checking whether the shop is open.
                                    date should be written using this format:
                                    {"year-month-date"}
                                    The date should be returned in plain text, not in JSON.
                                    """,
                        },
                        "new_time": {
                            "type": "string",
                            "description": f"""
                                    New time proposed by the user, use this for checking the time whether the reservation is available.
                                    time should be written using this format in 24 hours:
                                    {"HH:MM"}
                                    The time should be returned in plain text, not in JSON.
                                    """,
                        },
                        "new_service": {
                            "type": "string",
                            "description": f"""
                                    New service proposed by the user, use this for checking whether the service is available.
                                    The service should be returned in plain text, not in JSON.
                                    """,
                        },
                    },
                    "required": ["user_name", "date", "is_cancel"]
                },
            }
        },

        {
            "type": "function",
            "function": {
                "name": "make_reservation",
                "description": """
                            Use this function to make reservation for the customer, collect all necessary information from the user. 
                            Do not guess customer's name, phone number, if they are missing, ask for clarify. 
                """,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_name": {
                            "type": "string",
                            "description": """
                                        The customer's full name
                            """,
                        },
                        "date": {
                            "type": "string",
                            "description": f"""
                                    User proposed date, use this for checking whether the shop is open.
                                    date should be written using this format:
                                    {"YYYY-MM-DD"}
                                    The date should be returned in plain text, not in JSON.
                                    """,
                        },
                        "time": {
                            "type": "string",
                            "description": f"""
                                    User proposed time, use this for checking the time whether the reservation is available.
                                    time should be written using this format in 24 hours:
                                    {"HH:MM"}
                                    The time should be returned in plain text, not in JSON.
                                    """,
                        },
                        "service": {
                            "type": "string",
                            "description": f"""
                                        The name of the service that the user wish to order, only options avaliable from ask_database.
                                        The service should be returned in plain text, not in JSON.
                            """
                        },
                        "phoneNumber": {
                            "type": "string",
                            "description": f"""
                                    Customer's contact number
                                    phone number should be 10 digit number:
                                    The phone number should be returned in plain text, not in JSON.
                                    """
                        },
                        "specialist": {
                            "type": "string",
                            "description": f"""
                                    User preferred specialist, not a required input, only pass in when user is asking for.
                                    The specialist should be returned in plain text, not in JSON.
                                    """,
                        }
                    },
                    "required": ["user_name", "date", "time", "service","phoneNumber"]
                },
            }
        },]

        #open ai events, initailizing OpenAI prompt

        self.client = OpenAI()
        self.GPT_MODEL = "gpt-4.1-mini"

        today = date.today()
        formatted_date = today.strftime("%Y-%m-%d")
        weekday = today.strftime("%A")
        _query = "SELECT service_name, duration, price, discription FROM Services;"
        shop_menu = str(self.conn.execute(_query).fetchall())
        shop_info = str(self.conn.execute("SELECT Shop_name, Opening_Hours, Location, Specialists, General_Background, Contact_Info, Website FROM Shop_Info;").fetchall())
        user_name = None
        phone_number = None
        print(f"Today is {formatted_date}, which is a {weekday}.")
        self.messages = [
            {"role":"system",
            "content": "Your name is Lynx and you are a shop assistant, skilled in customer services. You should get the customer's first and last name, phone number, and services they want."},
            {"role": "system", "content": "Your answer should be as short as possible, avoid long sentences."},
            {"role": "system", "content": f"Today is {formatted_date}. Today is {weekday}."},
            {"role": "system", "content": f"Shop service menu: {shop_menu}"},
            {"role": "system", "content": f"Shop information: {shop_info}"},
            {"role": "system", "content": "You are not allowed to call any function until the user has explicitly provided their full name and phone number. Always ask the user if the required information is missing."},
            {"role": "system","content":"only use database information to answer questions. Do not speak anything unrelated to database information."},
            {"role": "system", "content": "Start with a greeting, and ask the user how you can help them today."},
            #{"role": "assistant", "content": "user name: " + str(user_name) + ", phone number: " + str(phone_number)},
            {"role":"user","content":"You are working for Herbal Nail Bar now, start by greeting to user and ask how you can help them today."}
            ]
        
        # turn this while loop into a function to start the conversation
    def start_conversation(self, user_input=None):
        """Start the conversation with the user."""
        #print(f"{openAI_log} Starting conversation with OpenAI...")
        # If user_input is provided, append it to messages
        if user_input:
            self.messages.append({"role": "user", "content": user_input})
            response = self.chat_completion_request(tools = self.aiTools)
            #print conversation result
            #create an exception phase in here, withdraw the bad input
            response_message = response.choices[0].message
            #print(response_message)
            self.messages.append(response_message)
            #check if tool is used:
            return self.ResponseManager(response_message)
            



    #SQLite methods

    #this is the actual program I/O for OpenAI to visit database
    def ask_database(self, query):
        """Function to query SQLite database with a provided SQL query."""
        try:
            results = str(self.conn.execute(query).fetchall())
        except Exception as e:
            results = f"query failed with error: {e}"
        return results




    def check_registration(self, name):
        output = self.calendar.get_appointments_by_customer(name)
        if not output:
            return "No registration found."
        return f"Customer {name} has Registration found: {output}"

    #We dont check specialist at this point, since we only have one specialist table
    def check_calendar(self, date, time, specialist=None):
        output = self.calendar.check_appointment_availability(date, time, specialist)
        #print(output)
        return str(output)
        

    #func that will return the next solution
    def make_reservation(self, user_name, phoneNumber, date, time, service, specialist = None):
        """Function to make reservation for user by accessing SQLite database."""
        print("user name: " + user_name, "phone number: " + phoneNumber, "date: " + date, "time: " + time, "service: " + service, "specialist: " + specialist)
        if((user_name == None) | (phoneNumber == None) | (date == None) | (service == None)):
            return ("Ask the user to provide all missing information.")
        
        returnCode = self.calendar.add_appointment(user_name, phoneNumber, date, time, service, specialist)
        if(returnCode == 0):
            return ("Tell the user the reservation has been complete, ask if more help is needed.")
        elif(returnCode == 1):
            return ("Service is not offered by the shop, find the similar service from database and clarify with the user.")
        elif(returnCode == 2):
            return ("Outside business hours, ask the user to choose another time, or tell the user what time is avaliable.")
        elif(returnCode == 3):
            return ("All specialists are booked, ask for another time or wait.")
        else:
            return ("Tell the user that an unexpected error occured, visit shop website to see more details.")

    #disabled feature
    def change_reservation(self, name, date, is_cancel=False, time=None, new_date=None, new_time=None, new_service=None):
        """Function to change reservation for user by accessing SQLite database."""
        print("user name: " + name, "date: " + date, "time: " + time)
        if(name == None):
            return ("Ask the user to provide full name.")
        if (time == None | date == None):
            return ("Run the check_registration function to get the user's appointment information, then ask the user which appointment they want to change.")
        if (new_date == None | new_time == None | new_service == None):
            return ("Ask the user to provide all missing information for the new appointment.")
        #call calendar manager change appointment method
        returnCode = self.calendar.change_appointment(name, date, time, new_date, new_time, new_service, is_cancel)
        if(returnCode == 0):
            return ("Tell the user the reservation has been successfully changed.")
        elif(returnCode == 1):
            return ("No reservation found for this user, ask for more details.")
        elif(returnCode == 2):
            return ("Service is not offered by the shop, find the similar service from database and clarify with the user.")
        elif(returnCode == 3):
            return ("Outside business hours, ask the user to choose another time, or tell the user what time is avaliable.")
        elif(returnCode == 4):
            return ("All specialists are booked, ask for another time or wait.")
        else:
            return ("Tell the user that an unexpected error occured, visit shop website to see more details.")



    #This Print message is for call without tools
    def printMessage(self):
        model_response_with_function_call = self.client.chat.completions.create(
        model = self.GPT_MODEL,
        messages=self.messages,
    )
        print("printMessage log: ", model_response_with_function_call.choices[0].message.content)
        return model_response_with_function_call.choices[0].message.content

    #print the first message:
    #printMessage()

    #try the function for 3 times before declare failure
    # Try the function 3 times before declaring failure
    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    def chat_completion_request(self, tools=None, tool_choice="auto"):
        try:
            response = self.client.chat.completions.create(
                model=self.GPT_MODEL,
                messages=self.messages,
                tools=tools,
                tool_choice=tool_choice,
            )
            print("chat_completion_request:", response.choices[0].message.content)
            return response
        except Exception as e:
            print("chat_completion_request: Unable to generate ChatCompletion response")
            print(f"Exception: {e}")
            raise  # Let Tenacity handle the retries
        

    def ResponseManager(self, response_message):
        #print(response_message.tool_calls[0])
        tool_calls = response_message.tool_calls
        
        if tool_calls:
            #if true the model will return the name of the tool / 
            # function ot call and the arugment(s)
            tool_call = tool_calls[0]
            tool_call_id = tool_calls[0].id
            tool_function_name = tool_call.function.name

            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError as e:
                print(f"{openAI_log} Error decoding JSON arguments: {e}")
                return "An error has occurred: Invalid function arguments."
            #we might need to set another condition to check if tool_calls valid for 
            if tool_function_name == 'make_reservation':
                #make reservation func
                required_fields = ['user_name', 'phoneNumber', 'date', 'time', 'service']
                missing_fields = [field for field in required_fields if field not in args]
                if missing_fields:
                    results = ("Missing important information: " + ", ".join(missing_fields) + ". Please ask the user to provide all missing information.")
                else:
                    user_name = args.get('user_name', None)
                    phoneNumber = args.get('phoneNumber', None)
                    date = args.get('date', None)
                    time = args.get('time', None)
                    service = args.get('service', None)
                    specialist = args.get('specialist', "Any")

                    print(f"making reservation \n")
                    results = self.make_reservation(user_name, phoneNumber, date, time, service, specialist)
                    #print result
                
                self.messages.append({
                    "role":"tool",
                    "tool_call_id":tool_call_id,
                    "name":tool_function_name,
                    "content":results
                })

                return self.printMessage()

            elif tool_function_name == 'ask_database':
                tool_query_string = args['query']
                print(f"{openAI_log} checking database \n")
                results = self.ask_database(tool_query_string)

                self.messages.append({
                    "role":"tool",
                    "tool_call_id":tool_call_id,
                    "name": tool_function_name,
                    "content": results
                })

                # Invoke the chat completion API with the function response
                # appended to the messages list.
                # Messages with role 'tool' must be a response to a preceding message 
                # with 'tool_calls'.
                return self.printMessage()
            elif tool_function_name == 'check_calendar':
                date = args.get('date', None)
                time = args.get('time', "Any")
                specialist = args.get('specialist', "Any")
                #print(f"{date} {time} {specialist}")
                print(f"{openAI_log} checking calendar \n")
                results = self.check_calendar(date, time, specialist)
                self.messages.append({
                    "role":"tool",
                    "tool_call_id":tool_call_id,
                    "name": tool_function_name,
                    "content": results
                })
                return self.printMessage()
            else:
                print(f"{openAI_log} Error: function {tool_function_name} does not exist")
                return "An error has occurred: Function not found."
        else:
            #model did not identify a function to call, result can be returned to the user
            print(f"{openAI_log} {response_message.content}")
            return response_message.content



