import os
import json
import random
import string
from datetime import datetime
import dotenv

from user import User

from google_auth_oauthlib.flow import Flow

from flask import Flask, request, redirect, session, send_from_directory

dotenv.load_dotenv()

app = Flask(__name__)
app.static_folder = 'static'

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/oauth2callback', methods=['GET'])
def oauth_redirect():
    if request.args.get('error'):
        return f'<h1>Fatal error</h1>\n<a href="https://t.me/TgCalendarTheBot">Retry</a>'
    
    code = request.args.get('code')
    if code is None:
        return f'<h1>Fatal error</h1>\n<a href="https://t.me/TgCalendarTheBot">Retry</a>'
    
    short_code = ''.join(
        random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(10)) # FIXME
    User.save_oauth_code(code, short_code, datetime.now())
    
    return redirect(f'https://telegram.me/TgCalendarTheBot?start=oauth-{short_code}')

SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/userinfo.profile']
GOOGLE_CREDENTIALS_PATH = 'credentials/google.json'

# Create an OAuth 2.0 flow object
flow = Flow.from_client_secrets_file(GOOGLE_CREDENTIALS_PATH, SCOPES)
flow.redirect_uri = os.getenv('OAUTH_REDIRECT_URI')

def get_url():
    return flow.authorization_url(access_type='offline', include_granted_scopes='true', prompt='consent')[0]

def save(user: User, code):
    try:
        flow.fetch_token(code=code)
        credentials = flow.credentials
        credentials = json.loads(credentials.to_json())
    except Exception as e:
        print(e)
        return False
    
    user.save_credentials(credentials)
    return True
 
def main():
    app.run(host='127.0.0.1', port=5000, debug=True)

if __name__ == '__main__':
    main()