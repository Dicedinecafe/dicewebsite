import os
from flask import Flask, request, jsonify, redirect, render_template
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pathlib import Path

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Verify required environment variables
required_vars = ['SPOTIPY_CLIENT_ID', 'SPOTIPY_CLIENT_SECRET', 'SPOTIPY_REDIRECT_URI']
if not all(os.getenv(var) for var in required_vars):
    missing = [var for var in required_vars if not os.getenv(var)]
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

# Spotify OAuth configuration
sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="user-modify-playback-state user-read-playback-state",
    cache_path=".spotify_cache"
)

def get_spotify_client():
    """Get authenticated Spotify client or None if not logged in"""
    token_info = sp_oauth.get_cached_token()
    return spotipy.Spotify(auth=token_info['access_token']) if token_info else None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    try:
        token_info = sp_oauth.get_access_token(request.args.get('code'))
        return redirect('/')
    except Exception as e:
        return f"Authentication failed: {str(e)}", 400

@app.route('/search')
def search():
    if not (sp := get_spotify_client()):
        return jsonify({'error': 'Not authenticated'}), 401
    
    if not (query := request.args.get('q')):
        return jsonify({'error': 'Missing search query'}), 400

    try:
        results = sp.search(query, type='track', limit=5)
        return jsonify([{
            'name': track['name'],
            'artists': ', '.join(artist['name'] for artist in track['artists']),
            'uri': track['uri'],
            'image': track['album']['images'][0]['url'] if track['album']['images'] else None
        } for track in results['tracks']['items']])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/queue', methods=['POST'])
def add_to_queue():
    if not (sp := get_spotify_client()):
        return jsonify({'error': 'Not authenticated'}), 401
    
    if not (track_uri := request.json.get('track_uri')):
        return jsonify({'error': 'Missing track_uri'}), 400

    try:
        sp.add_to_queue(track_uri)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True)  # Using port 5001 to avoid conflicts