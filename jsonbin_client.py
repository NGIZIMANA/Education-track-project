
import requests
import os

class JSONBinClient:
    def __init__(self, master_key=None):
        self.master_key = master_key or os.environ.get("JSONBIN_MASTER_KEY")
        if not self.master_key:
            raise ValueError("JSONBIN_MASTER_KEY not set. Please provide it or set the environment variable.")
        self.base_url = "https://api.jsonbin.io/v3/b"

    def _headers(self):
        return {
            "Content-Type": "application/json",
            "X-Master-Key": self.master_key
        }

    def create_bin(self, data, bin_name=None, private=True):
        headers = self._headers()
        if bin_name: headers["X-Bin-Name"] = bin_name
        headers["X-Bin-Private"] = "true" if private else "false"
        response = requests.post(self.base_url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()["metadata"]

    def read_bin(self, bin_id):
        headers = self._headers()
        response = requests.get(f"{self.base_url}/{bin_id}", headers=headers)
        response.raise_for_status()
        return response.json()["record"]

    def update_bin(self, bin_id, data):
        headers = self._headers()
        response = requests.put(f"{self.base_url}/{bin_id}", json=data, headers=headers)
        response.raise_for_status()
        return response.json()["record"]

    def delete_bin(self, bin_id):
        headers = self._headers()
        response = requests.delete(f"{self.base_url}/{bin_id}", headers=headers)
        response.raise_for_status()
        return response.json()

    def list_bins(self):
        # JSONBin.io v3 API does not directly support listing all bins without a collection.
        # This functionality might need to be simulated or a collection used.
        # For now, we'll assume specific bin IDs are known or managed externally.
        raise NotImplementedError("Listing all bins is not directly supported by JSONBin.io v3 without collections.")

