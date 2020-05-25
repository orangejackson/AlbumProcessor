import re
import requests
from bs4 import BeautifulSoup
#from datetime import date
import datetime
import pyperclip

def tdFormat(td: datetime.timedelta) -> str:
	if td.seconds >= 3600:
		return "%d:%02d:%02d" % (td.seconds // 3600, td.seconds % 3600 // 60, td.seconds % 3600 % 60)
	else:
		return "%d:%02d" % (td.seconds // 60, td.seconds % 60)

targetDir = r"C:\Users\Sterculius\Downloads\Cemetery Piss"

userAgent = "Mozilla/5.0"
#userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36"

#band = "Vader"
#targetUrlMain = "https://www.metal-archives.com/search?searchString=" + band + "&type=band_name"
targetUrlMain = "https://www.metal-archives.com/bands/Vader/145"
#targetUrlMain = "https://www.metal-archives.com/bands/Behemoth/263"
targetUrlMain = "https://www.metal-archives.com/bands/Cemetery_Piss/3540352141"
targetUrlMain = "https://www.metal-archives.com/bands/Skeletonwitch/16879"

targetUrlDiscography = "https://www.metal-archives.com/band/discography/id/" + re.search("\/(\d+)$", targetUrlMain).group(1) + "/tab/all"

targetUrlBaseLyrics = "https://www.metal-archives.com/release/ajax-view-lyrics/id/"

band = {}

response = requests.get(targetUrlMain, headers = { "User-Agent": userAgent })
soup = BeautifulSoup(response.text, "html.parser")

band["Name"] = soup.find("h1", class_="band_name").text.strip()

headerFieldText = []
headerValueText = []

for i in soup.find("div", id="band_stats").find_all("dt"):
	headerFieldText.append(re.sub(":$", "", i.text.strip()))

for i in soup.find("div", id="band_stats").find_all("dd"):
	headerValueText.append(i.text.strip())

headerDetails = dict(zip(headerFieldText, headerValueText))

if len(headerDetails["Location"]) > 0:
	band["Location"] = headerDetails["Location"] + ", " + headerDetails["Country of origin"]
else:
	band["Location"] = headerDetails["Country of origin"]

band["Genre"] = headerDetails["Genre"]
band["LyricalThemes"] = headerDetails["Lyrical themes"]
band["Formed"] = headerDetails["Formed in"]
band["Status"] = headerDetails["Status"]
band["YearsActive"] = headerDetails["Years active"]
band["CurrentLabel"] = headerDetails["Current label"]

band["Releases"] = []

band["ScrapeDate"] = datetime.date.today()

response = requests.get(targetUrlDiscography, headers = { "User-Agent": userAgent })
soup = BeautifulSoup(response.text, "html.parser")

releaseTableHeaders = soup.find("table").find_all("th")
releaseHeaders = [releaseTableHeaders[i].text.strip() for i in range(len(releaseTableHeaders))]
releaseTableRows = soup.find("table").find("tbody").find_all("tr")

for releaseRow in releaseTableRows:
	releaseRowCells = releaseRow.find_all("td")
	
	rowData = {}
	
	for i,cell in enumerate(releaseRowCells):
		rowData[releaseHeaders[i]] = cell

	band["Releases"].append({
		"Title": rowData["Name"].text.strip(),
		"Year": int(rowData["Year"].text.strip()),
		"Type": rowData["Type"].text.strip(),
		"Url": rowData["Name"].find("a")["href"].strip(),
		"Tracks": []
		})

for release in band["Releases"]:
	response = requests.get(release["Url"], headers = { "User-Agent": userAgent })
	soup = BeautifulSoup(response.text, "html.parser")

	headerFieldText = []
	headerValueText = []

	for i in soup.find("div", id="album_info").find_all("dt"):
		headerFieldText.append(re.sub(":$", "", i.text.strip()))

	for i in soup.find("div", id="album_info").find_all("dd"):
		headerValueText.append(i.text.strip())

	headerDetails = dict(zip(headerFieldText, headerValueText))

	#release["ReleaseDate"] = headerDetails["Release date"]
	try:
		release["ReleaseDate"] = datetime.datetime.strptime(re.sub("(\d)(?:st|nd|rd|th)","\\1",headerDetails["Release date"]), "%B %d, %Y").strftime("%Y-%m-%d")
	except ValueError as err:
		try:
			release["ReleaseDate"] = datetime.datetime.strptime(headerDetails["Release date"], "%B %Y").strftime("%Y-%m")
		except ValueError as err:
			release["ReleaseDate"] = datetime.datetime.strptime(headerDetails["Release date"], "%Y").strftime("%Y")

	release["Label"] = headerDetails["Label"]
	release["CatalogID"] = headerDetails["Catalog ID"]
	release["Format"] = headerDetails["Format"]

	trackRows = soup.find("table",class_="display table_lyrics").find_all("tr", class_=lambda s: s is not None and ("even" in s or "odd" in s))

	for row in trackRows:
		lyrics = ""

		if re.search("Show lyrics", row.text) is not None:
			lyricsID = row.find_all("td")[0].find("a")["name"].strip()
			
			response = requests.get(targetUrlBaseLyrics + lyricsID, headers = { "User-Agent": userAgent })
			soup = BeautifulSoup(response.text, "html.parser")

			lyrics = re.sub("\r","",soup.text.strip())

		if len(row.find_all("td")[2].text.strip()) > 0:
			lengthMatches = re.search("(?:(\d{1,2}):)?(\d{1,2}):(\d{1,2})",row.find_all("td")[2].text.strip())
			length = datetime.timedelta(hours = 0 if lengthMatches.group(1) is None else int(lengthMatches.group(1)),
								minutes = 0 if lengthMatches.group(2) is None else int(lengthMatches.group(2)),
								seconds = 0 if lengthMatches.group(3) is None else int(lengthMatches.group(3)))
		else:
			length = datetime.timedelta()
			
		release["Tracks"].append({ "Number": int(re.sub(".$","", row.find_all("td")[0].text.strip())),
							"Title": re.sub("\n", " ", row.find_all("td")[1].text).strip(),
							"Length": length,
							"Lyrics": lyrics
							})

print("Name:\t\t%s" % band["Name"])
print("-" * 40)
print("Location:\t%s" % band["Location"])
print("Genre:\t\t%s" % band["Genre"])
print("Lyrical Themes:\t%s" % band["LyricalThemes"])
print("Formed:\t\t%s" % band["Formed"])
print("Status:\t\t%s" % band["Status"])
print("Years Active:\t%s" % band["YearsActive"])
print("Current Label:\t%s" % band["CurrentLabel"])
print("-" * 40)

for i,release in enumerate(band["Releases"]):
	print("%02d - %s - %s (%s) [%d] / [%s]" % (i + 1, band["Name"], release["Title"], release["Type"], release["Year"], release["ReleaseDate"]))#.strftime("%Y-%m-%d")))
	for track in release["Tracks"]:
		print("\t%02d - %s (%s) - Lyrics: %i chars" % (track["Number"], track["Title"], tdFormat(track["Length"]), len(track["Lyrics"])))
	print("")

pass