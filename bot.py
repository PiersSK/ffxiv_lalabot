# bot.py
import os
import random
import json
import math

import discord
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
Houses = json.load(open("./houses.json", "r")) # {"Uldah": [], "Limsa": [], "Gridania": [], "Kugane": []}
Responses = json.load(open("./responses.json", "r")) 
Todos = json.load(open("./todo.json", "r")) 


Recoverable_House = {
    "Location": None
    ,"House": None
}

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user: # Don't respond to yourself!!!!
        return
    if message.content[0] != "\\": # Commands start with a backslash
        return
    
    command = message.content.split(" ")[0].replace("\\", "")
    args = message.content.replace(message.content.split(" ")[0]+" ", "").split(" ")
    print(f"Command detected from {message.author}: {command}")
    response = Responses["errors"]["default"]

    if command == 'addhouse':
        if validate_command(args, 4, [str, int, int, str, int]):
            response = add_house(args)
        else:
            response = Responses["errors"]["addhouse"]["default"]
    if command == 'gethouses':
        response = get_houses()
    if command == 'delhouse':
        if validate_command(args, 2, [str, int]):
            response = del_house(args)
        else:
            response =  Responses["errors"]["delhouse"]["default"]
    if command == 'recoverhouse':
        response = recover_house()
    if command == 'help':
        response = Responses["help"]["default"]
    if command == 'addtodo':
        if validate_command(args, 1, [str]):
            print(args)
            print(args[0])
            response = add_todo([" ".join(args)], message.author)
        else:
            response = Responses["errors"]["default"]
    if command == 'deltodo':
        if validate_command(args, 1, [int]):
            print(args)
            print(args[0])
            response = del_todo(args, message.author)
        else:
            response = Responses["errors"]["default"]
    if command == 'todos':
        show_hidden = args[0] != "\todos"
        response = get_todos(show_hidden)
    await message.channel.send(response)

# @args - [] - the input
# @mandatory_args - int - min number of args that must be present
# @arg_types - type[] - the types of each arg
def validate_command(args, mandatory_args, arg_types):
    if len(args) < mandatory_args:
        return False
    
    for i, arg_type in enumerate(arg_types):
        if len(args) > i:
            if arg_type is int:
                try:
                    int(args[i])
                except:
                    return False
            elif arg_type is str:
                continue
    
    return True

def add_todo(args, author):
    message = args[0]
    Todos.append({
        "message": message,
        "user": f"{author}",
        "active": True,
        "timeadded": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "answered": ""
    })
    update_todos()
    return "To-Do added"

def del_todo(args, author):
    todo_index = int(args[0])
    Todos[todo_index]["active"] = False
    Todos[todo_index]["answered"] = f"{author}"
    update_todos()
    return "To-Do Completed!"

def get_todos(show_hidden):
    message = ""
    for i, item in enumerate(Todos):
        if item['active'] or show_hidden:
            message += f"{i}: \"{item['message']}\" requested by {item['user']} at {item['timeadded']}."
            if not item['active'] and show_hidden:
                message += f" Answered by {item['answered']}"
            message += "\n"
    if message == "":
        message = "Sorry, no To-Dos found!"
    return message
        


def add_house(args):
    # Get args: [location, ward, plot, price]
    location = args[0].lower().capitalize()
    uptime_mod = 0 if len(args) < 5 else abs(int(args[4]))
    first_seen = datetime.now() - timedelta(hours = uptime_mod)

    house = {
            "Ward": int(args[1])
            ,"Plot": int(args[2])
            ,"Price": args[3]
            ,"First Seen": first_seen.strftime("%Y-%m-%d %H:%M:%S")
    }

    valid_locations = ["ULDAH", "LIMSA", "GRIDANIA", "KUGANE"] 
    for loc in valid_locations: # Adjust for shorthand
        if loc[0] == location:
            location = loc.lower().capitalize()

    # default response message
    response = Responses["success"]["addhouse"].format(location)

    # Extra validity checks
    location_valid = location.upper() in valid_locations
    ward_valid = house["Ward"] >= 0 and house["Ward"] <= 21
    plot_valid = house["Plot"] >=0 and house["Plot"] <= 60

    if location_valid and ward_valid and plot_valid:
        for existing_house in Houses[location]:
            if existing_house["Ward"] == house["Ward"] and existing_house["Plot"] == house["Plot"]:
                response = Responses["errors"]["addhouse"]["duplicate"] + f" ({get_house_uptime(existing_house)} ago)"
                return response

        Houses[location].append(house)
        update_houses()
    else:
        response = Responses["errors"]["addhouse"]["default"]

    # updatehouses()
    return response

def get_house_uptime(house):
    first_seen = datetime.strptime(house["First Seen"], "%Y-%m-%d %H:%M:%S")
    uptime = int((datetime.now() - first_seen).total_seconds())

    uptime_hours = math.floor(uptime/3600)
    uptime_msg = "" if uptime_hours == 0 else f"{uptime_hours}h"
    uptime -= uptime_hours*3600

    uptime_mins = math.floor(uptime/60)
    uptime_msg += "" if uptime_mins == 0 else f"{uptime_mins}m"
    uptime -= uptime_mins*60

    uptime_msg += f"{uptime}s"

    return uptime_msg

def get_houses():
    update_houses()
    msg = ""
    for loc in Houses:
        if not Houses[loc]:
            continue
        for i, house in enumerate(Houses[loc]):
            uptime_msg = get_house_uptime(house)
            msg = msg + f"{i}: {loc} - Ward {house['Ward']}, Plot {house['Plot']} for {house['Price']} gil. First spotted {uptime_msg} ago\n"

    if msg == "":
        msg = Responses["errors"]["gethouses"]["default"]
    return msg

def del_house(args):
    location = args[0]
    house_index = int(args[1])
    valid_locations = ["ULDAH", "LIMSA", "GRIDANIA", "KUGANE"] 
    for loc in valid_locations: # Adjust for shorthand
        if loc[0] == location:
            location = loc.lower().capitalize()
    
    if location.upper() not in valid_locations:
        return Responses["errors"]["delhouse"]["default"]
    
    Recoverable_House["Location"] = location
    Recoverable_House["House"] = Houses[location][house_index]
    del Houses[location][house_index]
    update_houses()
    return f"Removed house -> {location} - Ward {Recoverable_House['House']['Ward']}, Plot {Recoverable_House['House']['Plot']}. This can be recovered with \\recoverhouse"

def recover_house():
    if Recoverable_House["Location"] and Recoverable_House["House"]:
        Houses[Recoverable_House["Location"]].append(Recoverable_House["House"])
        response = Responses["success"]["recoverhouse"].format(Recoverable_House["Location"])
        Recoverable_House["Location"] = None
        Recoverable_House["House"] = None
    else:
        response = Responses["errors"]["recoverhouse"]["default"]
    
    update_houses()
    return response

def update_houses():
    for loc in Houses:
        if not Houses[loc]:
            continue
        new_houses = []
        for house in Houses[loc]:
            if datetime.now() - datetime.strptime(house["First Seen"], "%Y-%m-%d %H:%M:%S") < timedelta(hours = 24):
                new_houses.append(house)
        Houses[loc] = new_houses
    
    with open("./houses.json", "w") as houses_file:
        json.dump(Houses, houses_file)

def update_todos():
    with open("./todo.json", "w") as todos_file:
        json.dump(Todos, todos_file)

client.run(TOKEN)