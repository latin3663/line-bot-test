# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import os
import sys
from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
)
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_binary
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import urllib.request
import requests
from datetime import datetime
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (MessageEvent, TextMessage, MessageAction,
                            TemplateSendMessage, ButtonsTemplate)
import psycopg2

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
DATABASE_URL = os.getenv('DATABASE_URL', None)
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
user_id = os.getenv('USER_ID', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)


@app.route("/")
def index():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM car_stock.line_user_id")
            userIdRows = cur.fetchall()

    messages = TextMessage(text="Hello world!!")
    line_bot_api.push_message(userIdRows, messages)
    return "hello world"


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    if event.type == "message":
        profile = line_bot_api.get_profile(event.source.user_id)
        messages = TextMessage(text="メッセージイベントを取得しました。\nYour ID:" +
                               profile.user_id)
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM car_stock.line_user_id where user_id = " +
                    id)
                userIdRow = cur.fetchone()
                # 未登録のユーザーなら登録しておく
                if userIdRow is None:
                    insertSql = "INSERT INTO car_stock.line_user_id VALUES (" + profile.user_id + ")"
                    # INSERT文 実行
                    cur.execute(insertSql)
                    # INSERT をコミット
                    conn.commit()
                
    elif event.type == "follow":
        messages = TextMessage(text="フォローイベントを取得しました。\nYour ID:" +
                               profile.user_id)

    status_msg = profile.status_message
    if status_msg != "None":
        # LINEに登録されているstatus_messageが空の場合は、"なし"という文字列を代わりの値とする
        status_msg = "なし"

    # messages = TemplateSendMessage(alt_text="Buttons template",
    #                                template=ButtonsTemplate(
    #                                    thumbnail_image_url=profile.picture_url,
    #                                    title=profile.display_name,
    #                                    text=f"User Id: {profile.user_id[:5]}...\n"
    #                                         f"Status Message: {status_msg}",
    #                                    actions=[MessageAction(label="成功", text="次は何を実装しましょうか？")]))

    line_bot_api.reply_message(event.reply_token, messages=messages)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
