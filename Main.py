import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from openai import OpenAI
import requests
from PIL import Image 
import base64

# Enter your OpenAI key
OPENAI_API_KEY = ""

#To configure your spotipy authorization run the following commands in terminal:
#export SPOTIPY_CLIENT_ID='your-spotify-client-id'
#export SPOTIPY_CLIENT_SECRET='your-spotify-client-secret'
#export SPOTIPY_REDIRECT_URI='your-app-redirect-url'


scope = "user-library-read"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

def GeneratePrompt (API_KEY, songs):
    """
    function that returns a prompt for DALL-E and a playlist name for a given set of songs

    INPUTS
    API_KEY: (str) OpenAI API Key
    songs: (str) songs in format "song1, song2, song3..."

    RETURNS
    Dictionary of {"prompt": (prompt for DALL-E) and "name" : (playlist name)}
    """
    client = OpenAI(api_key = API_KEY)
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Generate a prompt for DALL-E or a similar image generation software to create an image that represents these songs: " + songs}
    ]
    )
    prompt = completion.choices[0].message.content

    #generate the playlist name
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Generate the name of a playlist that includes these songs: "}
    ]
    )
    name = completion.choices[0].message.content

    return {"prompt": prompt, "name": name}

def GenerateImage (API_KEY, prompt):
    """
    
    """
    client = OpenAI(api_key = API_KEY)
    response = client.images.generate(
    model="dall-e-3",
    prompt=prompt,
    size="1024x1024",
    quality="standard",
    n=1,
    )

    image_url = response.data[0].url

    
    return image_url


def UrlToB64 (image_url, name = "MyPlaylistImage"):
    """takes a image url, downloads the image as jpg and returns a Base_64 file of the image"""

    img_data = requests.get(image_url).content
    with open(name + '.jpg', 'wb') as handler:
        handler.write(img_data)
    
    # open method used to open different extension image file 
    im = Image.open(r"./" + name+'.jpg')  
    
    # This method will show image in any image viewer  
    im.show()

    img = base64.b64encode(requests.get(image_url).content)

    return img


def createSongList (playlist_id):
    """
    returns a string of the songs within the given playlist

    INPUT
    playlist_is: (str) spotify playlist id

    RERTURN
    string of songs
    """
    playlist = sp.playlist_tracks(playlist_id)
    songs = ""
    for song in playlist["items"]:
        songs += song["track"]["name"] # retrieve the song name
        songs += " by "
        songs += song["track"]["artists"][0]["name"] # parse the nested dictionaries/lists to find the artist name
        songs += ", "
    songs= songs[:-2]
    return songs
    


#iterate through the playlists printing the names and saving the ids
playlists = sp.current_user_playlists()
name_to_id = {}
for i in playlists["items"]:
    print(i["name"])
    name_to_id[i["name"]] = i["id"]

#ask the user for a playlist to use
playlist_name = input("Type the name of the playlist you wish to select: ")
while playlist_name not in name_to_id:
    print("Invalid input")
    playlist_name = input("Type the name of the playlist you wish to select: ")
playlist_id = name_to_id[playlist_name] # retrieve the id

# get the songs in string form
songs = createSongList(playlist_id)

#retrieve the DALLE prompt and playlist name suggestion
prompt_name_dict = GeneratePrompt(OPENAI_API_KEY, songs)
prompt = prompt_name_dict["prompt"]

#generate cover image and convert to Base64
image_url = GenerateImage(OPENAI_API_KEY, prompt)
img = UrlToB64(image_url, name = playlist_name)

#Ask the user if they want to change their playlist cover
change_image = input("do you want me to change your playlist image? [y/n]: ")
while change_image not in "ynYN":
    print("invalid response")
    input("do you want me to change your playlist image? [y/n]: ")

#if they say yes change the cover 
if change_image in "yY":
    sp.playlist_upload_cover_image(playlist_id, img)
    print("Done!")
#otherwise print image saved to files
else:
    print("image saved to files")
