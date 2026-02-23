from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

HTML_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YT Downloader App</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="flex items-center justify-center min-h-screen p-4" style="background-color: #111827; color: white; font-family: sans-serif;">
    <div class="rounded-xl shadow-lg p-6 w-full max-w-md" style="background-color: #1f2937; padding: 24px; border-radius: 12px; width: 100%; max-width: 450px; margin: 0 auto; box-sizing: border-box; border: 1px solid #374151;">
        <h1 class="text-2xl font-bold text-center mb-6" style="text-align: center; color: #ef4444; font-size: 24px; margin-bottom: 20px;"><i class="fab fa-youtube"></i> YT Downloader App</h1>
        
        <input type="text" id="url" placeholder="Paste YouTube Link here..." style="width: 100%; padding: 14px; margin-bottom: 16px; background: #374151; color: white; border: 1px solid #4b5563; border-radius: 8px; box-sizing: border-box; font-size: 16px;">
        
        <button onclick="getLinks()" id="btn" style="width: 100%; background: #dc2626; color: white; padding: 14px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 16px;">
            <i class="fas fa-search"></i> Get Download Links
        </button>
        
        <div id="loading" style="display: none; text-align: center; margin-top: 24px; color: #9ca3af;">
            <i class="fas fa-spinner fa-spin" style="font-size: 30px; color: #ef4444; margin-bottom: 10px;"></i>
            <p>Extracting links... Please wait.</p>
        </div>
        
        <div id="result" style="display: none; margin-top: 24px;">
            <div style="background: #374151; padding: 12px; border-radius: 8px; margin-bottom: 12px; border: 1px solid #4b5563;">
                <p style="font-size: 12px; color: #9ca3af; text-transform: uppercase; margin-bottom: 4px;">Video Title</p>
                <p id="title" style="font-weight: bold; line-height: 1.4;"></p>
            </div>
            <a id="vid" target="_blank" style="display: block; width: 100%; text-align: center; background: #2563eb; color: white; padding: 14px; border-radius: 8px; text-decoration: none; margin-bottom: 12px; box-sizing: border-box; font-weight: bold;"><i class="fas fa-video mr-2"></i> Download MP4 Video</a>
            <a id="aud" target="_blank" style="display: block; width: 100%; text-align: center; background: #9333ea; color: white; padding: 14px; border-radius: 8px; text-decoration: none; box-sizing: border-box; font-weight: bold;"><i class="fas fa-music mr-2"></i> Download Audio Only</a>
        </div>
        
        <p id="error" style="display: none; color: #fca5a5; background: rgba(239,68,68,0.2); padding: 12px; border-radius: 8px; margin-top: 16px; text-align: center; border: 1px solid #f87171;"></p>
    </div>

    <script>
        async function getLinks() {
            const url = document.getElementById('url').value;
            if(!url) return;
            document.getElementById('btn').style.opacity = '0.5';
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
            document.getElementById('error').style.display = 'none';
            try {
                const res = await fetch('/api/download?url=' + encodeURIComponent(url));
                const data = await res.json();
                if(data.error) throw new Error(data.error);
                document.getElementById('title').innerText = data.title;
                document.getElementById('vid').href = data.video_url || '#';
                document.getElementById('aud').href = data.audio_url || '#';
                document.getElementById('result').style.display = 'block';
            } catch(e) {
                document.getElementById('error').innerText = "Error: " + e.message;
                document.getElementById('error').style.display = 'block';
            } finally {
                document.getElementById('btn').style.opacity = '1';
                document.getElementById('loading').style.display = 'none';
            }
        }
    </script>
</body>
</html>
"""

def get_download_links(url):
    ydl_opts = {'quiet': True, 'skip_download': True, 'noplaylist': True, 'ignoreerrors': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info: raise Exception("Failed to extract info")
        best_mp4 = next((f for f in info.get("formats", []) if f.get("ext") == "mp4" and f.get("vcodec") != "none" and f.get("acodec") != "none"), None)
        best_audio = next((f for f in info.get("formats", []) if f.get("vcodec") == "none" and f.get("acodec") != "none"), None)
        return {"title": info.get("title"), "video_url": best_mp4["url"] if best_mp4 else None, "audio_url": best_audio["url"] if best_audio else None}

@app.route('/')
def home():
    # render_template_string မသုံးတော့ဘဲ တိုက်ရိုက်ထုတ်ပြပါမယ်
    return HTML_CODE

@app.route('/api/download')
def download():
    url = request.args.get('url')
    if not url: return jsonify({"error": "No URL provided"}), 400
    try:
        return jsonify(get_download_links(url))
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
