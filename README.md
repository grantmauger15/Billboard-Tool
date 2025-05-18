## Billboard Hot 100 CLI tool
A simple command-line tool (CLI) to fetch songs from the Billboard Hot 100 chart in the form of Spotify URIs.

## Features
- Select songs that have appeared on the Billboard Hot 100 chart, using criteria such as year, peak position, overall chart dominance, and artist.
- Choose to retrieve either a list of song names or a list of Spotify URIs, ready to easily be pasted into a Spotify playlist.
- Order songs either chronologically or by how much they dominated the chart within the specified timeframe.
## Installation
### 1) Download the repository using CMD
```powershell
git clone "https://github.com/grantmauger15/Billboard-Hot-100-Tool.git"
cd Billboard-Tool
```
### 2) Run install.bat
```powershell
install.bat
```
### 3) Place Spotify API credentials in config.ini
```ini
[DEFAULT]
client_id=your_client_id_here
client_secret=your_client_secret_here
```

#### You can now access the tool by using the "bb" command in your preferred command line interface.
## Usage
Once installed, the tool can be used from anywhere in your terminal.
### Basic Commands
```bash
bb get -y 2024 -t 100 -c
```
- The above command will retrieve the top 100 charting songs on the Billboard Hot 100 in 2024, ordered by when they reached their peak position.
```bash
bb get -y 1990s -p 10- -a 'mariah carey'
```
- The above command will retrieve all Mariah Carey songs from the 1990s that peaked within the top 10 on the chart, ordered by chart dominance.
```bash
bb get -l
```
- Rather than placing Spotify URIs into the user's clipboard, the -l option saves a list of song names to the clipboard.
- This command will return every song that ever charted on the Billboard Hot 100, ordered by chart dominance. 
```bash
bb -h
```
- The -h flag can be applied to any command or subcommand to get more help with using the tool or learning more of the possible flags.