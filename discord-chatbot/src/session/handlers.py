import datetime

#Generates timestamp for logging
def timestamp():
    now = datetime.datetime.now()
    date_time = now.strftime("%d-%m-%Y_%H-%M-%S")

    return date_time


#Handler when failed to read history files from save location
def failed_to_load_history_files():
    print("HANDLED: Reloaded history files")


#Handler when connection to OpenAI API fails
def lost_API_connection():
    print("Error connecting to LLM")

def missing_API_key():
    print("Missing OpenAI API key")



