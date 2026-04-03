import requests

class JSONBinClient:
    def __init__(self, api_key, bin_id):
        self.api_key = api_key
        self.bin_id = bin_id
        self.url = f"https://api.jsonbin.io/v3/b/{bin_id}"

    def read_bin(self, bin_id):
        headers = {"X-Master-Key": self.api_key}
        res = requests.get(self.url, headers=headers)

        if res.status_code == 200:
            return res.json().get("record", {})
        return {}

    def update_bin(self, bin_id, data):
        headers = {
            "X-Master-Key": self.api_key,
            "Content-Type": "application/json"
        }
        requests.put(self.url, json=data, headers=headers)
