import os
from flask import Flask, request, redirect, session, render_template
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "dice_and_dine_secret"
app.config['SESSION_COOKIE_NAME'] = 'DiceQueueSession'

SCOPE = "user-read-playback-state user-modify-playback-state"

sp_oauth = SpotifyOAuth(
    scope=SCOPE,
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI")
)

@app.route("/")
def index():
    if "token_info" not in session:
        return redirect("/login")
    return render_template("index.html")

@app.route("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info
    return redirect("/")

@app.route("/add", methods=["POST"])
def add():
    token_info = session.get("token_info", None)
    if not token_info:
        return redirect("/login")
    sp = Spotify(auth=token_info['access_token'])
    query = request.form["song"]
    results = sp.search(q=query, limit=1, type="track")
    if results['tracks']['items']:
        track_uri = results['tracks']['items'][0]['uri']
        sp.add_to_queue(track_uri)
        return "🎵 Added to queue!"
    return "❌ Song not found."

if __name__ == "__main__":
    app.run(port=8888, debug=True)
