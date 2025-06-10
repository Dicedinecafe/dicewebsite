from flask import Flask, request, jsonify, redirect, session
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Needed for session

# Use environment variables for credentials
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

# Scope needed to modify playback queue
SCOPE = "user-modify-playback-state user-read-playback-state"

sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_path=".cache"  # Cache token locally in this file
)

def get_spotify_client():
    token_info = sp_oauth.get_cached_token()
    if not token_info:
        return None
    access_token = token_info['access_token']
    return spotipy.Spotify(auth=access_token)

@app.route('/login')
def login():
    # Redirect user (you) to Spotify login page
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    if not token_info:
        return "Could not get token", 400
    return "Login successful! You can now close this tab."

@app.route('/search')
def search():
    sp = get_spotify_client()
    if not sp:
        return jsonify({'error': 'Not authenticated. Please /login first.'}), 401

    q = request.args.get('q')
    if not q:
        return jsonify({'error': 'Missing query parameter q'}), 400

    results = sp.search(q, type='track', limit=5)
    tracks = results['tracks']['items']
    simplified = [{
        'name': t['name'],
        'artists': ', '.join([a['name'] for a in t['artists']]),
        'uri': t['uri']
    } for t in tracks]
    return jsonify(simplified)

@app.route('/add_to_queue', methods=['POST'])
def add_to_queue():
    sp = get_spotify_client()
    if not sp:
        return jsonify({'error': 'Not authenticated. Please /login first.'}), 401

    data = request.get_json()
    track_uri = data.get('track_uri')
    if not track_uri:
        return jsonify({'error': 'Missing track_uri'}), 400

    try:
        sp.add_to_queue(track_uri)
        return jsonify({'message': 'Track added to queue!'})
    except spotipy.exceptions.SpotifyException as e:
        return jsonify({'error': str(e)}), e.http_status

if __name__ == '__main__':
    app.run(debug=True)
