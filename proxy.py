from flask import Flask, jsonify
import requests
from urllib.parse import quote

app = Flask(__name__)

class Nse:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.nseindia.com/"
        })
        self.session.get("https://www.nseindia.com", timeout=5)

    def get_index_quote(self, symbol_name: str):
        encoded_symbol = quote(symbol_name)
        url = f"https://www.nseindia.com/api/equity-stockIndices?index={encoded_symbol}"
        r = self.session.get(url, timeout=5)
        data = r.json()
        for item in data.get("data", []):
            if item.get("index") == symbol_name:
                return {"lastPrice": item.get("lastPrice")}
        return {"lastPrice": None}

nse = Nse()

@app.route("/price/<symbol>")
def price(symbol):
    try:
        price_data = nse.get_index_quote(symbol)
        return jsonify(price_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
