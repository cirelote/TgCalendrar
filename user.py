import os
import json

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, create_engine, insert, update, delete
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from telegram import Message

from languages import en

Base = declarative_base()

CREDENTIALS_PATH = 'oauth/credentials'

class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)
    state = Column(String(50))
    language = Column(String(50))
    timezone = Column(String(50))
    
class Messages(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    message = Column(String(500))
    created_at = Column(DateTime)
     
class Cache_oauth_codes(Base):
    __tablename__ = 'cache_oauth_codes'
    code = Column(String(50), primary_key=True, nullable=False)
    short_code = Column(String(50))
    created_at = Column(DateTime)
    
class Cache_calendar_page_tokens(Base):
    __tablename__ = 'cache_calendar_page_tokens'
    token = Column(String(50), primary_key=True, nullable=False)
    short_token = Column(String(50))
    
class Cache_calendar_event_ids(Base):
    __tablename__ = 'cache_calendar_event_ids'
    id = Column(Integer, primary_key=True, nullable=False)
    short_id = Column(String(50))
    
class Cache_drive_page_tokens(Base):
    __tablename__ = 'cache_drive_page_tokens'
    token = Column(String(50), primary_key=True, nullable=False)
    short_token = Column(String(50))

class User:
    def db_connect(self):
        self.engine = create_engine('sqlite:///database.db')
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        Base.metadata.create_all(self.engine)
        
    def __init__(self, user, language=None, state=None, timezone=None):
        self.db_connect()
        
        self.id = user.id
        self.name = user.name
        self.username = user.username
        
        if language is not None:
            self.set_language(language)
            
        if state is not None:
            self.set_state(state)
            
        if timezone is not None:
            self.set_timezone(timezone)
            
        insert_user = insert(Users).values(id=self.id, state=state, language=language).prefix_with("OR IGNORE")
        self.session.execute(insert_user)
        self.session.commit()
        
    @property
    def exists(self):
        '''
        Check if user language is set
        
        Returns:
            bool: True if language is set, False otherwise
        '''
        user = self.session.query(Users).filter(Users.id == self.id).first()
        
        return user is not None and user.language is not None
    
    @property
    def language(self):
        return self.session.query(Users).filter(Users.id == self.id).first().language
    
    def set_language(self, language):
        update_user = update(Users).where(Users.id == self.id).values(language=language).prefix_with("OR IGNORE")
        self.session.execute(update_user)
        self.session.commit()
    
    @property
    def timezone(self):
        return self.session.query(Users).filter(Users.id == self.id).first().timezone
    
    def set_timezone(self, timezone):
        update_user = update(Users).where(Users.id == self.id).values(timezone=timezone).prefix_with("OR IGNORE")
        self.session.execute(update_user)
        self.session.commit()
    
    @property
    def state(self):
        return self.session.query(Users).filter(Users.id == self.id).first().state
    
    def set_state(self, state):
        update_user = update(Users).where(Users.id == self.id).values(state=state).prefix_with("OR IGNORE")
        self.session.execute(update_user)
        self.session.commit()
        
    def getstr(self, str_code):
        lang = self.language
        if lang == 'en':
            return en.get(str_code)
        # if lang == 'uk':
        #     return uk.get(str_code)
        
    def load_credentials(self):
        with open(f'{CREDENTIALS_PATH}/{self.id}.json', 'r') as token:
            return json.load(token)    
    
    def save_credentials(self, credentials): # FIXME
        if not os.path.exists(CREDENTIALS_PATH):
            os.makedirs(CREDENTIALS_PATH)
            
        with open(f'{CREDENTIALS_PATH}/{self.id}.json', 'w') as token:
            json.dump(credentials, token)
    
    @property
    def logged_in(self):
        try:
            return self.credentials is not None
        except Exception as e:
            return False
    
    @property
    def credentials(self) -> dict:
        return self.load_credentials() if self.exists else None
    
    @staticmethod
    def save_oauth_code(code, short_code, created_at):
        session = sessionmaker(bind=create_engine('sqlite:///database.db'))()
        insert_code = insert(Cache_oauth_codes).values(code=code, short_code=short_code, created_at=created_at)
        session.execute(insert_code)
        session.commit()
        session.close()
        
    def get_oauth_code(self, short_code):
        return self.session.query(Cache_oauth_codes).filter(Cache_oauth_codes.short_code == short_code).first().code
    
    def delete_oauth_code(self, code):
        delete_code = delete(Cache_oauth_codes).where(Cache_oauth_codes.code == code)
        self.session.execute(delete_code)
        self.session.commit()
        
    @property
    def message_pool(self):
        # return all messages from the pool
        pool = self.session.query(Messages).filter(Messages.user_id == self.id).all()
        # return messages and date as a list of strings
        # return [f'{message.message}\n\nSent at: ({message.created_at})' for message in pool]
        return [f'{message.message}' for message in pool]
    
    def add_message_to_pool(self, message: Message):
        insert_message = insert(Messages).values(user_id=self.id, message=message.text, created_at=message.date)
        self.session.execute(insert_message)
        self.session.commit()
    
    def clear_message_pool(self):
        delete_messages = delete(Messages).where(Messages.user_id == self.id)
        self.session.execute(delete_messages)
        self.session.commit()
        
    def __del__(self):
        self.session.close()