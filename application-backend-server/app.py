from flask import Flask, jsonify, request
import time, requests, os
from jose import jwt
import pymysql
import json
import dns.resolver

ISSUER   = os.getenv("OIDC_ISSUER", "http://localhost/auth/realms/realm_sv001")
AUDIENCE = os.getenv("OIDC_AUDIENCE", "account")
JWKS_URL = os.getenv("OIDC_JWKS_URL", "http://authentication-identity-server:8080/auth/realms/realm_sv001/protocol/openid-connect/certs")

_JWKS = None; _TS = 0
def get_jwks():
    global _JWKS, _TS
    now = time.time()
    if not _JWKS or now - _TS > 600:
        response = requests.get(JWKS_URL, timeout=5)
        response.raise_for_status()
        _JWKS = response.json()
        _TS = now
    return _JWKS

app = Flask(__name__)

@app.get("/dns")
def dns_records():
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = ["10.10.10.53"]
    resolver.lifetime = 3
    records = []
    for name in ["web-frontend-server", "app-backend", "minio", "keycloak"]:
        fqdn = name + ".cloud.local"
        try:
            records.append({"name": fqdn, "addresses": [str(a) for a in resolver.resolve(fqdn, "A")]})
        except dns.exception.DNSException:
            return jsonify(error="DNS query failed", name=fqdn), 503
    return jsonify(records)

@app.get("/hello")
def hello(): return jsonify(message="Hello from App Server!")

@app.get("/secure")
def secure():
    auth = request.headers.get("Authorization","")
    if not auth.startswith("Bearer "):
        return jsonify(error="Missing Bearer token"), 401
    token = auth.split(" ",1)[1]
    try:
        payload = jwt.decode(token, get_jwks(), algorithms=["RS256"], audience=AUDIENCE, issuer=ISSUER)
        return jsonify(message="Secure resource OK", preferred_username=payload.get("preferred_username"))
    except Exception as e:
        return jsonify(error=str(e)), 401

@app.get("/student")
@app.get("/api/student")
def student():     
    if not os.path.exists("students.json"):
        return jsonify({"error": "File not found"}), 404
    
    with open("students.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)

@app.get("/students-db")
def students_db():
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "relational-database-server"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "root"),
        database="studentdb",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, student_id, fullname, dob, major FROM students")
            rows = cur.fetchall()
        for r in rows:
            r["dob"] = str(r["dob"])
        return jsonify(rows)
    finally:
        conn.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
