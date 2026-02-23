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
<body class="flex items-center justify-center min-h-screen p-4" style="background-color: #0f172a; color: white; font-family: sans-serif;">
    <div class="rounded-xl shadow-lg p-6 w-full max-w-md" style="background-color: #1e293b; padding: 24px; border-radius: 16px; border: 1px solid #334155;">
        <h1 class="text-2xl font-bold text-center mb-6" style="color: #ef4444;"><i class="fab fa-youtube"></i> YT Downloader</h1>
        
        <input type="text" id="url" placeholder="Paste YouTube Link here..." style="width: 100%; padding: 14px; margin-bottom: 16px; background: #334155; color: white; border: 1px solid #475569; border-radius: 10px; font-size: 16px; outline: none;">
        
        <button onclick="getLinks()" id="btn" style="width: 100%; background: #ef4444; color: white; padding: 14px; border: none; border-radius: 10px; font-weight: bold; cursor: pointer; font-size: 16px;">
            Get Download Links
        </button>
        
        <div id="loading" style="display: none; text-align: center; margin-top: 24px;">
            <i class="fas fa-circle-notch fa-spin" style="font-size: 32px; color: #ef4444; margin-bottom: 10px;"></i>
            <p style="color: #94a3b8;">Bypassing YouTube blocks... Please wait.</p>
        </div>
        
        <div id="result" style="display: none; margin-top: 24px;">
            <div style="background: #334155; padding: 12px; border-radius: 10px; margin-bottom: 12px; border: 1px solid #475569;">
                <p style="font-size: 11px; color: #94a3b8; text-transform: uppercase;">Title</p>
                <p id="title" style="font-weight: bold; font-size: 14px;"></p>
            </div>
            <a id="vid" target="_blank" style="display: block; width: 100%; text-align: center; background: #3b82f6; color: white; padding: 14px; border-radius: 10px; text-decoration: none; margin-bottom: 12px; font-weight: bold;">Download Video (MP4)</a>
            <a id="aud" target="_blank" style="display: block; width: 100%; text-align: center; background: #8b5cf6; color: white; padding: 14px; border-radius: 10px; text-decoration: none; font-weight: bold;">Download Audio (MP3/M4A)</a>
        </div>
        
        <p id="error" style="display: none; color: #f87171; background: rgba(239,68,68,0.1); padding: 12px; border-radius: 10px; margin-top: 16px; text-align: center; font-size: 13px;"></p>
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
                document.getElementById('error').innerText = e.message;
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
    # YouTube Block ကို ကျော်လွှားရန် ပိုမိုအားကောင်းသော Option များ
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'noplaylist': True,
        'ignoreerrors': True,
        # iOS/Android ဖုန်းမှကြည့်သလို ဟန်ဆောင်ခြင်း
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
        'referer': 'https://www.youtube.com/',
        'nocheckcertificate': True,
        # YouTube က IP Block တာကို လျှော့ချပေးနိုင်တဲ့ header 
        'http_headers': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        },
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # လင့်ခ်အချက်အလက်ကို ဆွဲယူခြင်း
            info = ydl.extract_info(url, download=False)
            if not info:
                raise Exception("YouTube is still blocking Render IP. Wait 5-10 mins and try again.")

            title = info.get("title", "Video")
            formats = info.get("formats", [])

            # ဒေါင်းလုဒ်လင့်ခ်များကို ရွေးထုတ်ခြင်း
            best_mp4 = next((f for f in formats if f.get("vcodec") != "none" and f.get("acodec") != "none" and f.get("ext") == "mp4"), None)
            best_audio = next((f for f in formats if f.get("acodec") != "none" and f.get("vcodec") == "none"), None)

            # Link မတွေ့လျှင် ပထမဆုံးရတဲ့ Link ကို ပေးမည်
            v_url = best_mp4["url"] if best_mp4 else (formats[0]["url"] if formats else None)
            a_url = best_audio["url"] if best_audio else v_url

            return {
                "title": title,
                "video_url": v_url,
                "audio_url": a_url
            }
    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg or "Sign in to confirm" in error_msg:
            return {"error": "YouTube blocked this IP. Please try a different video or wait a bit."}
        return {"error": error_msg}

@app.route('/')
def home():
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

@app.route('/')
def home():
    return HTML_CODE

@app.route('/api/download')
def download():
    url = request.args.get('url')
    if not url: return jsonify({"error": "No URL provided"}), 400
    try:
        return jsonify(get_download_links(url))
    except Exception as e:
        # Error အသေးစိတ်ကို UI မှာ ပြဖို့အတွက်ပါ
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
