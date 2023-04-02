import os
import base64
import html
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# 设置API范围
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def get_credentials():
    """获取OAuth2.0凭证"""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        creds.refresh(Request())
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def get_emails(counts=10):
    """获取邮件"""
    email_list = []
    try:
        # 获取OAuth2.0凭证
        creds = get_credentials()
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
            # 保存凭证到文件
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        # 创建Gmail API服务对象
        service = build('gmail', 'v1', credentials=creds)

        # 获取所有邮件的ID
        result = service.users().messages().list(userId='me').execute()
        messages = result.get('messages', [])
        # # 依次获取每封邮件的详细信息
        for message in messages[0:counts]:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            email_list.append(msg)

    except HttpError as error:
        print(f'An error occurred: {error}')
    return email_list


def parse_ironfish_mail(email):
    '''
    示例，解析某类特定的邮件
    :param email:
    :return:
        解析结果
    '''
    # 从邮件信息中获取主题和正文
    headers = email['payload']['headers']
    subject = next(h for h in headers if h['name'] == 'Subject')['value']
    body = email['snippet']

    try:
        recipient = next(h for h in headers if h['name'] == 'Delivered-To')['value']
    except:
        recipient='Unknown'
    try:
        orginal_recipient = next(h for h in headers if h['name'] == 'to')['value']
    except:
        orginal_recipient='Unknown'

    parts = email['payload'].get('parts')
    if parts:
        for part in parts:
            if part['mimeType'] == 'text/html':
                html_body = base64.urlsafe_b64decode(part['body']['data']).decode()
                body = html.unescape(html_body)
                break
    if 'Iron Fish' in subject:
        # 打印邮件主题和正文
        # print(f'Subject: {subject}')
        # print(f'sender: {sender}')
        # print(f'recipient: {recipient}')
        # print(f'orginal_recipient: {orginal_recipient}')
        # print(f'Body: {body}')
        # print('')
        link=find_string_in_text(body,'auth.magic',"challenge=false")
        r={
            'subject':subject,
            'recipient':recipient,
            'orginal_recipient':orginal_recipient,
            'link':'http://'+link
           }
        return r


def find_string_in_text(text, start, end):
    """在文本中查找以prefix开头，以suffix结尾的字符串"""
    start_index = text.find(start)
    if start_index != -1:
        end_index = text.find(end, start_index + len(start))
        if end_index != -1:
            return text[start_index:end_index + len(end)]
    return None


if __name__ == '__main__':
    emails=get_emails(10)
    if emails!=None:
        for email in emails:
            ppsd=parse_ironfish_mail(email)
            if ppsd!=None:
                print(ppsd)
