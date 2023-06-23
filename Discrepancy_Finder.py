import requests
import json
import tls_client
import pandas as pd
import webbrowser

# Set request headers
headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}

requests = tls_client.Session(client_identifier="chrome112")

# Fetch data from Prizepicks API
response1 = requests.get('https://api.prizepicks.com/projections')
prizepicks = response1.json()

# Fetch data from Underdog API
request = requests.get("https://api.underdogfantasy.com/beta/v3/over_under_lines")
underdog = request.json()

# Create empty lists to store player data
udlist = []
pplist = []
matchingnames = []

# Set to store unique player entries
unique_players = set()

# Dictionary to store PrizePicks player name mappings
library = {}

# Process Underdog API data
for appearances in underdog["over_under_lines"]:
    # Extract player name from the title
    underdog_title = ' '.join(appearances["over_under"]["title"].split()[0:2])
    colon_index = underdog_title.find(":")
    if colon_index != -1:
        underdog_title = underdog_title[colon_index + 1:].strip()
    UDdisplay_stat = appearances['over_under']['appearance_stat']['display_stat']
    UDstat_value = appearances['stat_value']
    uinfo = {"Name": underdog_title.lower(), "Stat": UDdisplay_stat, "Underdog": UDstat_value}
    udlist.append(uinfo)

# Process PrizePicks API data
for included in prizepicks['included']:
    PPname_id = included['id']
    PPname = included['attributes']['name']
    library[PPname_id] = PPname

for ppdata in prizepicks['data']:
    if '1st Half' in ppdata['attributes']['description']:
        continue
    PPid = ppdata['relationships']['new_player']['data']['id']
    PPprop_value = ppdata['attributes']['line_score']
    PPprop_type = ppdata['attributes']['stat_type']
    ppinfo = {"name_id": PPid, "Stat": PPprop_type, "Prizepicks": PPprop_value}
    pplist.append(ppinfo)

# Iterate over the pplist array to add player names and remove name_id
for element in pplist:
    name_id = element['name_id']
    if name_id in library:
        player_name = library[name_id]
        element['Name'] = player_name.lower()
    else:
        element['Name'] = "Unknown"
    del element['name_id']

# Compare player data from Underdog and PrizePicks
for udn in udlist:
    for ppn in pplist:
        if udn["Name"] == ppn["Name"] and udn["Stat"] == ppn["Stat"]:
            final = {
                "Name": udn["Name"],
                "Stat": udn["Stat"],
                "Underdog": udn["Underdog"],
                "Prizepicks": ppn["Prizepicks"]
            }
            matchingnames.append(final)

# Create a DataFrame from the matching names
rows = []
for match in matchingnames:
    name = match['Name']
    stat = match['Stat']
    underdog_value = match['Underdog']
    prizepicks_value = match['Prizepicks']
    rows.append((name, stat, underdog_value, prizepicks_value))
df = pd.DataFrame(rows, columns=['Name', 'Stat', 'Underdog', 'Prizepicks'])

# Convert column values to float for numeric comparison
df['Underdog'] = df['Underdog'].astype(float)
df['Prizepicks'] = df['Prizepicks'].astype(float)

# Filter the DataFrame based on the condition
filtered_df = df[abs(df['Underdog'] - df['Prizepicks']) >= 1.5]
filtered_df = filtered_df[filtered_df['Stat'] != 'Receiving Yards']

# Save the filtered DataFrame as an HTML file
filtered_df.to_html('matching_players.html', index=False)

# Open the HTML file in the Edge browser
webbrowser.open('matching_players.html', new=2)
