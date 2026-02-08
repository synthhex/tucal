# Server stuff.
from fastapi import FastAPI, Response
from fastapi_utilities import repeat_every
import httpx

# Module imports.
import logging
import filter


# Config loading.
import yaml
def load_config(file_path):
    try:
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
            return config
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found. Please define a cal.yaml file in the root folder!")
        quit()
    except yaml.YAMLError as exc:
        print(f"Error parsing YAML: {exc}")
        quit()

# Configuration
config = load_config('cal.yaml')
SOURCE_URL = config.get('source_url')
app = FastAPI()
calendars = {}

# Calendar refreshing logic.
@app.on_event("startup")
@repeat_every(seconds=60 * 60 * 24) # update source calendar every 24 hours
async def daily_refresh():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(SOURCE_URL)
            if response.status_code == 200:
                yaml_calendars = config.get('calendars').values() # get calendar definitions from config
                calendars.clear() # clear old calendars before updating
                calendars.update(filter.split_into_calendars(response.text, yaml_calendars))
                logging.info("Calendar updated successfully.")
        except Exception as e:
            logging.error(f"Failed to update calendar: {e}")

# Calendar serving logic.
@app.get("/tucal/calendar/{cal_name}")
async def serve_calendar(cal_name: str):
    if cal_name not in calendars:
        return Response(status_code=404, content="Calendar not found.")
    return Response(content=calendars[cal_name].to_ical(), media_type="text/calendar")