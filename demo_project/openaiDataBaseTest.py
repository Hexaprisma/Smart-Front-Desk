from openai import OpenAI
import sqlite3
import json

conn = sqlite3.connect("data/chinook/Chinook.db")
print("Opened database successfully")
client = OpenAI()

def get_table_names(conn):
    """Return a list of table names."""
    table_names = []
    #conn.execute is used to execute an SQL statement. It returns a cursor object 
    #that allows you to interate over the results of a query. 
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    for table in tables.fetchall():
        table_names.append(table[0])
        print(table[0])
    return table_names

def get_column_names(conn, table_name):
    """Return a list of column names."""
    column_names = []
    columns = conn.execute(f"PRAGMA table_info('{table_name}');").fetchall()
    for col in columns:
        column_names.append(col[1])
    return column_names

def get_database_info(conn):
    """Return a list of dicts containing the table name and column for each table in the database."""
    table_dicts = []
    for table_name in get_table_names(conn):
        column_names = get_column_names(conn, table_name)
        table_dicts.append({"table_name": table_name, "column_names": column_names})
    return table_dicts


database_schema_dict = get_database_info(conn)
database_schema_string = "\n".join(
    [
        f"Table: {table['table_name']}\nColumns:{', '.join(table['column_names'])}"
        for table in database_schema_dict
    ]
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "ask_database",
            "description": "Use this function to answer user questions about music. Input should be a fully formed SQL query.",
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
    }
]

def ask_database(conn, query):
    """Function to query SQLite database with a provided SQL query."""
    try:
        results = str(conn.execute(query).fetchall())
    except Exception as e:
        results = f"query failed with error: (e)"
    return results
"""
#verifying name extraction 
table_names = get_table_names(conn)
print("Tables:", table_names)

#close the connection
"""


messages = [{
    "role":"user",
    "content": "What is the name of the album with the most tracks?"
}]

response = client.chat.completions.create(
    model = 'gpt-3.5-turbo',
    messages = messages,
    tools = tools,
    tool_choice = "auto"
)

response_message = response.choices[0].message
messages.append(response_message)
print(response)

tool_calls = response_message.tool_calls
if tool_calls:
    #if true the model will return the name of the tool / 
    # function ot call and the arugment(s)
    tool_call_id = tool_calls[0].id
    tool_function_name = tool_calls[0].function.name
    tool_query_string = json.loads(tool_calls[0].function.arguments)['query']

    if tool_function_name == 'ask_database':
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
        model_response_with_function_call = client.chat.completions.create(
            model = "gpt-3.5-turbo",
            messages=messages,
        )
        print(model_response_with_function_call.choices[0].message.content)
    else:
        print(f"Error: function {tool_function_name} does not exist")
else:
    #model did not identify a function to call, result can be returned to the user
    print(response_message.content)

conn.close()

