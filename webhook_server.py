from flask import Flask, request
import subprocess
import hmac
import hashlib
import os

app = Flask(__name__)

GITHUB_SECRET = b'mysecret'  # тот, который вы задали в GitHub

def verify_signature(payload, signature):
    mac = hmac.new(GITHUB_SECRET, msg=payload, digestmod=hashlib.sha256)
    expected = 'sha256=' + mac.hexdigest()
    return hmac.compare_digest(expected, signature)

@app.route('/update', methods=['POST'])
def webhook():
    signature = request.headers.get('X-Hub-Signature-256', '')
    if not verify_signature(request.data, signature):
        return "Invalid signature", 403

    subprocess.Popen(["/home/ostrova_b/Ostrova_Bot/update.sh"])
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
