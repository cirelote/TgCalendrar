import json

from user import User

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/userinfo.profile']
CREDENTIALS_PATH = 'oauth/credentials'

class gCalendar:
    def __init__(self, user: User):
        self.user = user
        self.credentials = Credentials.from_authorized_user_file(f'{CREDENTIALS_PATH}/{user.id}.json', SCOPES)
        
        # Refresh the token if it's expired
        if self.credentials.expired:
            self.credentials.refresh(Request())
            with open(f'{CREDENTIALS_PATH}/{user.id}.json', 'w') as token:
                token.write(self.credentials.to_json())
        
        self.service = build(
            'calendar',
            'v3', 
            credentials=self.credentials,
            cache_discovery=False)
        
        if not self.service:
            raise Exception('Failed to create service')

    # def list(self):
    #     return self.service.events().list(calendarId='primary').execute()

    def create(self, summary, description, start, end):
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start,
                'timeZone': self.service.settings().get(setting='timezone').execute()['value'],
            },
            'end': {
                'dateTime': end,
                'timeZone': self.service.settings().get(setting='timezone').execute()['value'],
            },
        }
        return self.service.events().insert(calendarId='primary', body=event).execute()

    def delete(self, event_id):
        return self.service.events().delete(calendarId='primary', eventId=event_id).execute()