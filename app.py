from flask import Flask, request, jsonify, redirect
import yt_dlp

app = Flask(__name__)

@app.route('/ytomnix=<video_id>')
def get_stream(video_id):
    if not video_id:
        return jsonify({"error": "No video ID provided"}), 400
        
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # We want the best format, prioritizing m3u8 (HLS) which has all quality options for live streams!
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'simulate': True, # Get direct URL without downloading
        'extractor_args': {
            'youtube': {
                'player_client': ['tv', 'web_embedded'], # Try embedded and TV clients to avoid bot block
                'live_from_start': True,
                'skip': ['webpage', 'configs'] # Skip webpage to bypass bot protection
            }
        },
        'headers': {
            'Origin': 'https://www.youtube.com',
            'Referer': 'https://www.youtube.com/',
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            stream_url = info.get('url')
            
            # For live streams, YouTube provides an m3u8 manifest (HLS)
            # This manifest contains ALL quality profiles (1080p, 720p, 480p etc)
            is_live = info.get('is_live') or info.get('live_status') == 'is_live'
            
            if 'formats' in info:
                # Always try to find the master m3u8 first (best for ExoPlayer, supports all qualities)
                for f in info['formats']:
                    if f.get('ext') == 'm3u8' or f.get('protocol') in ['m3u8', 'm3u8_native']:
                        # The URL containing 'm3u8' is the master playlist
                        stream_url = f.get('url')
                        break
                
                # If no m3u8 is found, fallback to the best combined mp4
                if not stream_url or stream_url == info.get('url'):
                    for f in reversed(info['formats']):
                        if f.get('ext') == 'mp4' and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                            stream_url = f.get('url')
                            break
                            
            if stream_url:
                # HTTP 302 Redirect directly to the stream link
                # When ExoPlayer hits this URL, it will be automatically redirected to the actual .m3u8 link
                print(f"Redirecting to: {stream_url[:100]}...")
                return redirect(stream_url, code=302)
            else:
                return jsonify({"error": "Could not extract stream URL"}), 404
                
    except Exception as e:
        print(f"Error extracting {url}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return jsonify({
        "status": "active",
        "message": "Omnix API is running!",
        "usage": "/ytomnix=<video_id>"
    })

if __name__ == '__main__':
    # Run locally
    print("Omnix YouTube API Server running...")
    app.run(host='0.0.0.0', port=5000)
