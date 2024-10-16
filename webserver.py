from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Discord bot ok"

def run():
    # Use the PORT environment variable provided by Render, with a fallback to 8080 for local development
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)  # Fix typo: "traget" to "target"
    t.start()