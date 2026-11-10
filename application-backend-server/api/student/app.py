from flask import Flask, jsonify
import json
import os

app = Flask(__name__)

@app.get("/student")
def student():     
    if not os.path.exists("students.json"):
        return jsonify({"error": "File not found"}), 404
    
    with open("students.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)