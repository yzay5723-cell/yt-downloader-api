from flask import Flask, request, jsonify, render_template_string
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
<body class="bg-gray-900 text-white flex items-center justify-center min-h-screen p-4">
    <div class="bg-gray-800 rounded-xl shadow-lg p-6 w-full max-w-md">
        <h1 class="text-2xl font-bold text-center mb-6 text-red-500"><i class="fab fa-youtube"></i> YT Downloader App</h1>
        <input type="text" id="url" placeholder="Paste YouTube Link..." class="w-full p-3 rounded bg-gray-700 text-white mb-4 outline-none border border-gray-600 focus:border-red-500">
        <button onclick="getLinks()" id="btn" class="w-full bg-red-600 hover:bg-red-700 p-3 rounded font-bold transition flex justify-center items-center gap-2">
            <i class="fas fa-search"></i> Get Download Links
        </button>
        <div id="loading" class="hidden text-center mt-6 text-gray-400"><i class="fas fa-spinner fa-spin text-3xl mb-2 text-red-500"></i><p>Extracting links... Please wait.</p></div>
        <div id="result" class="hidden mt-6 space-y-4">
            <div class="bg-gray-700 p-3 rounded border border-gray-600"><p class="text-xs text-gray-400 uppercase tracking-wider mb-1">Video Title</p><p id="title" class="font-semibold text-sm"></p></div>
            <a id="vid" target="_blank" class="block text-center bg-blue-600 hover:bg-blue-700 p-3 rounded font-bold transition"><i class="fas fa-video mr-2"></i> Download MP4 Video</a>
            <a id="aud" target="_blank" class="block text-center bg-purple-600 hover:bg-purple-700 p-3 rounded font-bold transition"><i class="fas fa-music mr-2"></i> Download Audio Only</a>
        </div>
        <p id="error" class="hidden mt-4 bg-red-500/20 border border-red-500/50 text-red-400 p-3 rounded text-sm text-center"></p>
    </div>
    <script>
        async function getLinks() {
            const url = document.getElementById('url').value;
            if(!url) return;
            document.getElementById('btn').disabled = true;
            document.getElementById('loading').classList.remove('hidden');
            document.getElementById('result').classList.add('hidden');
            document.getElementById('error').classList.add('hidden');
            try {
                // Local URL အစား အလိုအလျောက်ချိတ်ဆက်မည့် Relative URL ပြောင်းထားပါသည်
                const res = await fetch('/api/download?url=' + encodeURIComponent(url));
                const data = await res.json();
                if(data.error) throw new Error(data.error);
                document.getElementById('title').innerText = data.title;
                document.getElementById('vid').href = data.video_url || '#';
                document.getElementById('aud').href = data.audio_url || '#';
                document.getElementById('result').classList.remove('hidden');
            } catch(e) {
                document.getElementById('error').innerText = "Error: " + e.message;
                document.getElementById('error').classList.remove('hidden');
            } finally {
                document.getElementById('btn').disabled = false;
                document.getElementById('loading').classList.add('hidden');
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
    return render_template_string(HTML_CODE)

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
