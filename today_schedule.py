#!/usr/bin/env python
# coding: utf-8



from __future__ import print_function
from linebot import LineBotApi
from linebot.models import TextSendMessage
import datetime
import pickle
import os.path
import re
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


SCOPES = ['https://www.googleapis.com/auth/calendar']

#Googleにcalenderへのアクセストークンを要求してcredsに格納
creds = None

#有効なトークンをすでに持っているかチェック(二回目以降の実行時に認証を省略するため)
if os.path.exists('token.pickle'):
    with open('token.pickle','rb') as token:
        creds = pickle.load(token)
#期限切れのトークンを持っているかチェック(認証を省略するため)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refreshtoken:
        creds.refresh(Request())
        
    #アクセストークンを要求
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',SCOPES)
        creds = flow.run_local_server()
    #アクセストークン保存(2回目以降の実行時に認証を省略するため)
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)
        
service = build('calendar', 'v3', credentials=creds)


#今日の一日のスケジュールを取得
def TodaysSchedule():
    #現在時刻を取得
    today_start = str(datetime.date.today()) + 'T00:00:00' + 'Z' 
    today_end = str(datetime.date.today()) + 'T23:59:59' 'Z'  
    #カレンダーから予定を取得

    events_result = service.events().list(calendarId='primary', timeMin=today_start,timeMax=today_end,
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
    events = events_result.get('items',[])
    
    today_events = []
    #予定がない場合はNot found
    if not events:
        #print('No upcoming events found.')
        return today_events
    #予定があった場合には、出力
    for event in events:
        start = event['start'].get('dateTime',event['start'].get('date'))
        start = start.split('T')
        start_date = start[0].split('-')
        date = '/'.join(start_date[1:])
        start_time = re.match('[0-9]{2}:[0-9]{2}',start[1]).group()

        end = event['end'].get('dateTime',event['end'].get('date'))
        end = end.split('T')
        end_time = re.match('[0-9]{2}:[0-9]{2}',end[1]).group()
        
        summary = [start_time+'～'+end_time+' '+event['summary']]
        
        today_events.extend(summary)
        #print(date,start_time+'-'+end_time, event['summary'])
    return today_events

#LINE APIリクエスト
file = open('info.json','r')
info = json.load(file)
CHANNEL_ACCESS_TOKEN = info['CHANNEL_ACCESS_TOKEN']
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)


#LINEにチャットを送る
def main():
    USER_ID = info['USER_ID']
    messages = TextSendMessage(text="おはようございます!")
    line_bot_api.push_message(USER_ID,messages=messages)
    
    today_events = []
    if not today_events:
        messages = TextSendMessage(text="今日は特に予定はございません!\n自由な1日をお過ごしください。")
        line_bot_api.push_message(USER_ID,messages=messages)
    else:
        event_messages = '本日のスケジュールは、\n'
        for event in today_events:
            event_messages += event+'\n'
        event_messages+='です！'
        messages = TextSendMessage(text=event_messages)
        line_bot_api.push_message(USER_ID,messages=messages)

    
if __name__ == "__main__":
    main()






