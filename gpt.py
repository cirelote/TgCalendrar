import json
import datetime

from flask import Flask, request, redirect, session

from openai import OpenAI

app = Flask(__name__)

OPENAI_API_KEY = json.load(open('credentials/openai.json'))['api_key']

client = OpenAI(api_key=OPENAI_API_KEY)

@app.route('/gpt-3', methods=['POST'])
def gpt_3():
    data = request.json
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": 
                f"""You'll be given text messages. Your goal is to create a JSON info for calndar event. Provide summary, description, start and end time (in ISO 8601 format). \n\n So return a JSON like ('summary': '...', 'description': '...', 'start': '...', 'end': '...'). If you can't extract summary return 'SUMMARY_ERROR'. If you can't extract description return 'DESCRIPTION_ERROR'. If you can't extract start and end time, return 'TIME_ERROR'. 
                
                Look for info using following rules:
                
                1. For summary look for the message that contains the most important info about the event.
                
                2. For description just expand the summary a bit.
                
                3. For start and end time look for the messages that contain the time of the event.
                
                Language: ukr. 
                
                Use short answers. 
                
                Додаткова інформація:
                
                В тексті може бути багато абревіатур які відносяться до навчальних предметів.

                time now - {datetime.datetime.now().isoformat()}

                Перша пара - 8:30
                Друга: 10:25
                Третя: 12:20
                Четверта: 14:15
                """},
            {"role": "user", "content": 'Here goes messages separated by "---": \n' + '\n---\n'.join(data['tg_messages'])}
        ]
    )
    print(response.choices[0].message.content)
    return response.choices[0].message.content

def main():
    app.run(host='127.0.0.1', port=5001, debug=True)
    
if __name__ == '__main__':
    main()