import dotenv
import os
import requests

from user import User
from gcalendar import gCalendar
import oauth

import logging
from telegram import Update, CallbackQuery
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ExtBot
import telegram.ext.filters as filters
from google.auth.exceptions import RefreshError

dotenv.load_dotenv('.env')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def start(update: Update, _):
    user = User(update.message.from_user)
    
    if 'oauth-' in update.message.text:
        short_code = update.message.text.replace('/start oauth-', '')
        code = user.get_oauth_code(short_code)
        if oauth.save(user, code):
            user.delete_oauth_code(code)
    
    if not user.exists:
        text = (
            'Hi! Send me a message, and I’ll try to add it to your Google Calendar.\n'
            'To get started, please select your language:'
        )
        
        await update.message.reply_text(
            text=text,
            reply_markup={
                'inline_keyboard': [
                    [
                        {'text': 'English', 'callback_data': 'l@en'}
                    ],
                    [
                        {'text': 'Українська', 'callback_data': 'l@ukr'}
                    ]
                ]}
            )
        return
    
    await update.message.reply_text(f'Hi, {user.name}! Send me a message, and I’ll try to add it to your Google Calendar.')
        
    await update.message.reply_text(
        text=user.getstr('start'),
        parse_mode='HTML',
        reply_markup={
            'keyboard': [
                [
                    {'text': user.getstr('create_event_button'), 'callback_data': 'create_event'},
                    {'text': user.getstr('clear_pool_button'), 'callback_data': 'clear_pool'}
                ],
                [
                    {'text': user.getstr('settings_button'), 'callback_data': 'settings'},
                    {'text': user.getstr('help_button'), 'callback_data': 'help'}
                ]
            ],
            'resize_keyboard': True,
            'one_time_keyboard': False
            }
        )
    
async def message_handler(update: Update, _):
    user = User(update.message.from_user)
    message_text = update.message.text
    
    if not user.exists:
        text = (
            'Hi! Send me a message, and I’ll try to add it to your Google Calendar.\n'
            'To get started, please select your language:'
        )
        
        await update.message.reply_text(
            text=text,
            reply_markup={
                'inline_keyboard': [
                    [
                        {'text': 'English', 'callback_data': 'l@en'}
                    ],
                    [
                        {'text': 'Українська', 'callback_data': 'l@ukr'}
                    ]
                ]}
            )
        
    if not user.logged_in and user.exists:
        # change text to ask for sign in
        await update.message.reply_text(
            text=user.getstr('sign_in'),
            parse_mode='HTML',
            reply_markup={
                'inline_keyboard': [
                    [
                        {'text': user.getstr('sign_in_button'), 'url': oauth.get_url()}
                    ]
                ]}
            )
        
        return
    
    if message_text == user.getstr('create_event_button'):
        try:
            calendar = gCalendar(user)
            info = requests.post(
                url='http://127.0.0.1:5001/gpt-3',
                json={'tg_messages': user.message_pool}
                ).json()
            summary = info['summary']
            description = info['description']
            
            if summary == 'SUMMARY_ERROR' or description == 'DESCRIPTION_ERROR':
                await update.message.reply_text(
                    text=user.getstr('create_event_few_info_error'),
                    parse_mode='HTML'
                )
                return
            
            if info['start'] == 'TIME_ERROR' or info['end'] == 'TIME_ERROR':
                await update.message.reply_text(
                    text=user.getstr('create_event_time_error'),
                    parse_mode='HTML'
                )
                return
            
            event = calendar.create(
                summary=summary,
                description=description,
                start=info['start'],
                end=info['end']
            )
            
            if event:
                # send alert that the event was created
                await update.message.reply_text(
                    text=user.getstr('create_event_completed'),
                    parse_mode='HTML',
                    reply_markup={
                        'inline_keyboard': [
                            [
                                {'text': user.getstr('view_event_button'), 'url': event['htmlLink']}
                            ]
                        ]}
                    )
                
                user.clear_message_pool()
                
            return
        except RefreshError:
            await update.message.reply_text(
                text=user.getstr('refresh_error'),
                parse_mode='HTML',
                reply_markup={
                    'inline_keyboard': [
                        [
                            {'text': user.getstr('sign_in_button'), 'url': oauth.get_url()}
                        ]
                    ]}
            )
            return
    
    if message_text == user.getstr('clear_pool_button'):
        user.clear_message_pool()
        await update.message.reply_text(
            text=user.getstr('clear_pool_completed'),
            parse_mode='HTML'
        )
        return
    
    if message_text == user.getstr('settings_button'):
        return
    
    if message_text == user.getstr('help_button'):
        return
    
    # Add message to pool only if the message is not a command
    user.add_message_to_pool(update.message)

async def home(cb: CallbackQuery):
    user = User(cb.from_user)
    if not user.exists:
        return
    
    await cb.message.edit_text(
        text=user.getstr('start'),
        parse_mode='HTML',
        reply_markup={
            'inline_keyboard': [
                [
                    {'text': user.getstr('create_event_button'), 'callback_data': 'create_event'},
                    {'text': user.getstr('clear_pool_button'), 'callback_data': 'clear_pool'}
                ],
                [
                    {'text': user.getstr('settings_button'), 'callback_data': 'settings'},
                    {'text': user.getstr('help_button'), 'callback_data': 'help'}
                ]
            ]}
        )
    
async def callback_handler(update: Update, _):
    cb = update.callback_query
    user = User(cb.from_user)
    
    # Change language
    if 'l@' in cb.data:
        user.set_language(cb.data.replace('l@', ''))
        await home(cb)
        return
            
    if cb.data == 'home':
        await home(cb)
        return
            
    # If any callback data is received, and the user is not logged in, ask for sign in
    if not user.logged_in and user.exists:
        # change text to ask for sign in
        await cb.message.edit_text(
            text=user.getstr('sign_in'),
            parse_mode='HTML',
            reply_markup={
                'inline_keyboard': [
                    [
                        {'text': user.getstr('sign_in_button'), 'url': oauth.get_url()}
                    ]
                ]}
            )
        
        return
        
    if cb.data == 'sign_in': # FIXME
        ExtBot.answer_callback_query(
            callback_query_id=cb.id,
            url='telegram.me/your_bot?start=XXXX'
        )
        return
    
    if cb.data == 'create_event':
        return

def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT, message_handler))
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    application.run_polling()
    
if __name__ == '__main__':
    main()