from icalendar import Calendar
import re

def split_into_calendars(input: str, calendar_definitions: list[dict]):
    """Splits the source calendar into multiple calendars based on regex matches."""
    output_calendars = {}
    cal = Calendar.from_ical(input)

    # Create new calendars for each definition.
    for cal_def in calendar_definitions:
        url = cal_def["url"]
        output_calendars[url] = init_with_headers(cal, cal_def)
    
    # Default calendar containing all subcalendars.
    output_calendars["default"] = init_with_headers(cal, {
        "name": "Default Calendar",
        "desc": "Default Calendar"
    })

    # Go through each event and parse it into the correct calendar.
    for event in cal.walk('VEVENT'):
        for cal_def in calendar_definitions:
            regex = cal_def["regex"]
            if re.search(regex, event.get('DESCRIPTION', '')): # check if the description matches the calendar regex
                event.color = cal_def.get("color", "white") # default color if not specified
                output_calendars[cal_def["url"]].add_component(event)
                output_calendars["default"].add_component(event)
                break # first calendar takes priority

    return output_calendars

def init_with_headers(cal: Calendar, definition: dict):
    """Initializes a calendar with the correct prodid and name."""
    new_cal = Calendar()
    
    # Add new headers.
    new_cal.add('prodid', f'-//TUCal Proxy//{definition["name"]}//EN')
    new_cal.add('version', '2.0')
    new_cal.add('X-WR-CALNAME', definition['name'])
    new_cal.add('X-WR-CALDESC', definition['name'])
    
    # Old headers begone. Leave my personal info alone.
    protected_keys = ['PRODID', 'VERSION', 'X-WR-CALNAME', 'X-WR-CALDESC', 'BEGIN', 'END']    
    for key, value in cal.items():
        if key.upper() not in protected_keys:
            new_cal.add(key, value)
            
    # Add the timezone components.
    for component in cal.walk('VTIMEZONE'):
        new_cal.add_component(component)
        
    return new_cal