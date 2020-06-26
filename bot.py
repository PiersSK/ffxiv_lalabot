# bot.py
import os
import random
import json
import math
import requests

import discord
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
API_CORE_URL = "https://garlandtools.org/db/doc/core/en/3/data.json"
CORE_DB = requests.get(API_CORE_URL).json()
API_SEARCH_URL = "https://garlandtools.org/api/search.php?text={}&lang=en"
API_ITEM_URL = "https://garlandtools.org/db/doc/item/en/3/{}.json"
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
    print(f"{client.user.name} has connected to Discord!")

@client.event
async def on_message(message):
    if message.author == client.user: # Don't respond to yourself!!!!
        return
    if message.content[0] != "\\": # Commands start with a backslash
        return
    
    command = message.content.split(" ")[0].replace("\\", "")
    args = message.content.split()[1:]
    print(f"Command detected from {message.author}: {command}")

    if command == "addhouse":
        if validate_command(args, 4, [str, int, int, str, int]):
            response = add_house(args)
        else:
            response = Responses["errors"]["addhouse"]["default"]
    elif command == "gethouses":
        response = get_houses()
    elif command == "delhouse":
        if validate_command(args, 2, [str, int]):
            response = del_house(args)
        else:
            response =  Responses["errors"]["delhouse"]["default"]
    elif command == "recoverhouse":
        response = recover_house()
    elif command == "help":
        response = Responses["help"]["default"]
    elif command == "addtodo":
        if validate_command(args, 1, [str]):
            print(args)
            print(args[0])
            response = add_todo([" ".join(args)], message.author)
        else:
            response = Responses["errors"]["default"]
    elif command == "deltodo":
        if validate_command(args, 1, [int]):
            print(args)
            print(args[0])
            response = del_todo(args, message.author)
        else:
            response = Responses["errors"]["default"]
    elif command == "todos":
        show_hidden = args[0] != "\todos"
        response = get_todos(show_hidden)
        await message.channel.send(embed=response)
        return
    elif command == "isearch":
        if validate_command(args, 1, [str]):
            print(args)
            embed = isearch(" ".join(args))
            await message.channel.send(embed=embed)
            return
    elif command == "test":
        embed = discord.Embed(title="Title", description="Desc", color=0x00ff00)
        embed.add_field(name="Field1", value="hi", inline=False)
        embed.add_field(name="Field2", value="hi2", inline=False)
        await message.channel.send(embed=embed)
        return
    else:
        response = Responses["errors"]["default"]

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
    author = f"{author}".split("#")[0]
    message = args[0]
    Todos.append({
        "message": message,
        "user": author,
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
    message = discord.Embed(title="To Dos", description="A list of outstanding reminders and requests", color=0x00ff00)
    for i, item in enumerate(Todos):
        if item["active"]:
            message.add_field(name=f"{i}: {item['user']}", value=get_item_craft_reqs(item["message"]), inline=False)
    return message

########################## ITEM DB SEARCH ##########################
def search_item(search):
    search_response = requests.get(API_SEARCH_URL.format(search.replace(" ", "%20"))).json()
    for obj in search_response:
        if obj["type"] == "item":
                return obj
    return {}
def get_item(item_id):
    response = requests.get(API_ITEM_URL.format(item_id)).json()
    return response

def get_job(job_id):
    response = CORE_DB["jobs"]
    for job in response:
        if int(job["id"]) == int(job_id):
            return job["name"]
    return response

def get_unlock(partials, id):
    for item in partials:
        if int(item["id"]) == int(id):
            return item["obj"]["n"]

def isearch(item_name):
    item_info = search_item(item_name)
    if item_info:
        id = item_info["id"]
    else:
        print(f"WARNING: Couldn't find an item - {item_name}")
        return item_name

    iresponse = get_item(id)
    item = iresponse["item"]
    print(f"https://garlandtools.org/files/icons/item/{id}.png")
    message = discord.Embed(
        title=item["name"]
        ,description=f"Item Level {item['ilvl']}"
        ,color=0x39a0d4
    )

    message.set_thumbnail(url=f"https://garlandtools.org/files/icons/item/{item['icon']}.png")
    message.add_field(name="More Info...", value=get_item_craft_reqs(item_name), inline=False)
    # message.set_image("https://garlandtools.org/files/icons/item/30056.png")


    return message

def get_item_craft_reqs(item_name):    
    item_info = search_item(item_name)
    if item_info:
        id = item_info["id"]
    else:
        print(f"WARNING: Couldn't find an item - {item_name}")
        return item_name

    iresponse = get_item(id)
    item = iresponse["item"]

    msg = f"[{item['name']}](https://garlandtools.org/db/#item/{id})"

    if "craft" in item:
        job_name = get_job(item["craft"][0]["job"])
        job_lvl = item["craft"][0]["lvl"]
        msg += f" - {job_name} Lvl{job_lvl}"
        if "unlockId" in item["craft"][0]:
            unlock = get_unlock(iresponse["partials"], item["craft"][0]["unlockId"])
            msg += f" (Requires {unlock})"

    return msg
##############################################################################

def get_db_status(item):
    item = "_".join([x.capitalize() for x in item.split(" ")])
    r = requests.head(f"https://ffxiv.gamerescape.com/wiki/{item}")
    return r.status_code

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