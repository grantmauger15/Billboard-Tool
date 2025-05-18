import requests
from dateutil.parser import parse
from datetime import datetime
import re
import argparse
import pyperclip
import json
import sys
import os
import time
import spotipy
from spotipy.cache_handler import CacheFileHandler
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException
from rapidfuzz import fuzz
from configparser import ConfigParser

def get_path(file):
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), file)
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), file)

# Read config.ini and extract Spotify client credentials
config = ConfigParser()
config.read(get_path('config.ini'))
client_id = config["DEFAULT"]["client_id"]
client_secret = config["DEFAULT"]["client_secret"]


# Check if API credentials are not configured
if not client_id or not client_secret:
    print("❌ Error: Missing client_id or client_secret in config.ini")
    sys.exit(1)

# Set up Spotify OAuth manager and cache handler
cache_handler = CacheFileHandler(cache_path=get_path('.cache'))
oauth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret, cache_handler=cache_handler)

# Verify that API credentials work properly
try:
    # Initialize the Spotipy client
    sp = spotipy.Spotify(oauth_manager=oauth_manager)
    sp.search(q="test", limit=1)  # Minimal API call to trigger credential validation
except SpotifyException as e:
    print("❌ Spotify API authentication failed:", e)
    sys.exit(1)
except Exception as e:
    print("❌ Unexpected error:", e)
    sys.exit(1)

# Create the argument parser
parser = argparse.ArgumentParser(description='Billboard Hot 100 query tool')
subparsers = parser.add_subparsers(dest="command", help='Available commands')

get_parser = subparsers.add_parser("get", help='Retrieve a list of songs from Billboard.')
get_parser.add_argument('-y', '--year', type=str, default='1958-2100', help='Specify a year or ranges of years to select songs from (e.g. 2025, 2015-2019, 2010+, 1960s).')
get_parser.add_argument('-p', '--pos', type=str, default='1-100', help='Specify a peak position or range of peak positions to select songs from (e.g. 10-, 1-5, 100).')
get_parser.add_argument('-c', '--chrono', action='store_true', help='When this switch is turned on, songs will be outputted in chronological order rather than by overall chart dominance.')
get_parser.add_argument('-t', '--top', type=int, help='Specify an upper limit to the number of songs you want, prioritizing songs by chart dominance.')
get_parser.add_argument('-a', '--artists', type=str, help='Specify an artist or list of artists you want your songs to be by (e.g. "beatles, rolling stones", "mariah carey").')
get_parser.add_argument('-l', '--list', action='store_true', help='When this switch is turned on, output for each song will be in the form [ARTIST] - [TITLE] rather than Spotify URIs.')

args = parser.parse_args()

# Use RegEx to parse the year option
if args.year:
    if years := re.match(r'(\d{4})-(\d{4})$', args.year):
        y = [int(years.group(1)), int(years.group(2))]
    if years := re.match(r'\d{4}$', args.year):
        y = [int(years.group()), int(years.group())]
    if years := re.match(r'(\d{4})\+$', args.year):
        y = [int(years.group(1)), 2100]
    if years := re.match(r'(\d{4})-$', args.year):
        y = [1900, int(years.group(1))]
    if years := re.match(r'\d{3}0s$', args.year):
        y = [int(f'{years.group()[:3]}0'), int(f'{years.group()[:3]}9')]

if args.pos:
    if pos := re.match(r'(\d+)-(\d+)$', args.pos):
        p = [int(pos.group(1)), int(pos.group(2))]
    if pos := re.match(r'\d+$', args.pos):
        p = [int(pos.group()), int(pos.group())]
    if pos := re.match(r'(\d+)\+$', args.pos):
        p = [int(pos.group(1)), 100]
    if pos := re.match(r'(\d+)-$', args.pos):
        p = [1, int(pos.group(1))]


url = 'https://raw.githubusercontent.com/mhollingshead/billboard-hot-100/main/all.json'
charts = requests.get(url).json()

def get_track_url(query):
    # print(query)
    results = sp.search(q=query, type='track', limit=10)
    time.sleep(0.2)
    url = get_best_url(query, results)
    add_to_json(query, url)
    
    return url
    
def get_best_url(query, res):
    best_score = 0
    best_match = None

    for track in res['tracks']['items']:
        artists = ", ".join([artist['name'] for artist in track['artists']])
        name = re.sub(r'\(feat.+\)', '', track['name'].lower())
        name = re.sub(r'remaster.+', '', name)
        candidate = f"{artists} - {name}".lower()
        score = fuzz.ratio(candidate, query.lower())

        # print(f'\033[91m{candidate} - \033[92m{query} = \033[93m{score}')

        if score > best_score:
            best_score = score
            best_match = track

    return best_match['uri']

def add_to_json(query, url):
    with open(get_path('urls.json'), 'r') as f:
        urls = json.load(f)
    
    urls[query] = url
    with open(get_path('urls.json'), 'w') as f:
        json.dump(urls, f, indent=2)

def getTime(date):
    epoch = datetime(1970, 1, 1)
    return (parse(date) - epoch).total_seconds() 

def getSongs(years=[1958,2100], pos=[1,100], chrono=False, top=None, artist=None, list=False):
    songs = {}

    for chart in charts:
        date = getTime(chart['date'])
        year = int(chart['date'][:4])
        if not (years[0] <= year <= years[1]):
            continue
        for song in chart['data']:
            full_title = f"{song['artist'].lower().replace('featuring', '').replace(' with ', ' ').replace(' and ', ' ')} - {song['song'].lower()}"
            if full_title not in songs:
                songs[full_title] = {
                    "artist": song['artist'],
                    "title": song['song'],
                    "score": 0,
                    "peak": song['this_week'],
                    "peakDate": date
                }
            elif song['this_week'] < songs[full_title]['peak']:
                songs[full_title]['peak'] = int(song['this_week'])
                songs[full_title]['peakDate'] = date

            weight = 1/(song['this_week'] ** 1.5) # Lower chart position values contribute more score (1 / rank^1.5)
            songs[full_title]['score'] += weight

    top_songs = {k: v for k, v in songs.items() if v['peak'] in range(pos[0], pos[1]+1)}
    top_songs = sorted(top_songs, key=lambda k: songs[k]['score'], reverse=True)

    if artist:
        top_songs = [song for song in top_songs if any(a.lower() in re.match(r'(.+) -', song).group(1).lower() for a in artist.split(','))]

    top_songs = top_songs[:top]

    if chrono:
        top_songs = [song for song in sorted(songs, key=lambda k: songs[k]['peakDate'], reverse=False) if song in top_songs]
    
    if list:
        return top_songs
    
    return getLinks(top_songs)

with open(get_path('urls.json'), 'r') as f:
    links = json.load(f)

def getLinks(songs):
    out = []

    for i, song in enumerate(songs):
        print(f"Processing song {i+1} out of {len(songs)}")
        if song in links:
            out.append(links[song])
        else:
            out.append(get_track_url(song))

    return out
    

pyperclip.copy("\n".join(getSongs(y, p, args.chrono, args.top, args.artists, args.list)))
print("The songs have been copied to your clipboard.")