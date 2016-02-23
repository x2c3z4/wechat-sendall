#--*-- coding:utf-8 --*--
import requests, requests.utils, pickle
import httplib
import sys
import pprint
from bs4 import BeautifulSoup
import re, shutil, xml.dom.minidom, json
import netrc
import os.path, time
import random
from optparse import OptionParser

from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer
import threading

s = requests.Session()
s.headers.update({'User-Agent':
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.94 Safari/537.36',
                  'Connection': 'keep-alive',
                  'Content-type': 'application/x-www-form-urlencoded'})
def debugReq(r):
  pp = pprint.PrettyPrinter(indent=4)
  pp.pprint(r.status_code)
  # pp.pprint(r.request.__dict__)
  # print >>sys.stderr, r.text
  print >> sys.stderr, s.cookies.get_dict()

real_send = False
http_port = 5678

uuid = ''
redirect_uri = ''
base_uri = ''
skey = ''
wxsid = ''
wxuin = ''
pass_ticket = ''
deviceId = 'e000000000000000'
BaseRequest = {}

SyncKey = []
ContactList = []
ChatContactList = []
My = {}


def getUUID():
  global uuid
  # url = "https://login.weixin.qq.com/jslogin"
  # payload = {
  #   'redirect_uri':'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage',
  #   'appid': 'wx782c26e4c19acffb',
  #   'fun': 'new',
  #   'lang': 'zh_CN',
  #   '_': int(time.time()),
  # }
  # headers = {'content-type': 'text/javascript'}
  # r = s.get(url, data = payload, headers = headers)
  url = "https://login.weixin.qq.com/jslogin?appid=wx782c26e4c19acffb&redirect_uri=https%3A%2F%2Fwx.qq.com%2Fcgi-bin%2Fmmwebwx-bin%2Fwebwxnewloginpage&fun=new&lang=zh_CN&_=" + str(
      int(time.time()))
  r = s.get(url)
  # debugReq(r)
  # window.QRLogin.code = 200; window.QRLogin.uuid = "oZwt_bFfRg==";
  regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
  pm = re.search(regx, r.text)

  code = pm.group(1)
  uuid = pm.group(2)

  if code == '200':
    return True

  return False


def getQRImage():
  path = os.path.join(os.getcwd(), "qrcode.jpg")
  url = "https://login.weixin.qq.com/qrcode/" + uuid
  r = s.get(url, stream=True)
  # debugReq(r)
  if r.status_code == 200:
    with open(path, 'wb') as f:
      r.raw.decode_content = True
      shutil.copyfileobj(r.raw, f)
  import socket
  ip = [l
        for l in
        ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2]
          if not ip.startswith("127.")][:1],
         [[(sc.connect(('8.8.8.8', 80)), sc.getsockname()[0], sc.close())
           for sc in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]])
        if l][0][0]
  print "[+] Please open http://" + ip + ":" + str(http_port) + "/qrcode.jpg or open " + path

  time.sleep(1)


def waitForLogin():
  global redirect_uri, base_uri
  url = "https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?loginicon=true&uuid=%s&tip=0&r=-1746241605&_=%s" % (
      uuid, int(time.time()))

  r = s.get(url, stream=True)
  # debugReq(r)
  # print r.text

  data = r.text
  regx = r'window.code=(\d+);'
  pm = re.search(regx, data)

  code = pm.group(1)

  if code == '201':  # 已扫描
    print('[+] Scan success, please click confirm on your mobile phone')
    tip = 0
  elif code == '200':  # 已登录
    print('[+] Logging in ...')
    regx = r'window.redirect_uri="(\S+?)";'
    pm = re.search(regx, data)
    redirect_uri = pm.group(1) + "&fun=new&version=v2"
    base_uri = redirect_uri[:redirect_uri.rfind('/')]
    # # push_uri与base_uri对应关系(排名分先后)(就是这么奇葩..)
    # services = [
    #     ('wx2.qq.com', 'webpush2.weixin.qq.com'),
    #     ('qq.com', 'webpush.weixin.qq.com'),
    #     ('web1.wechat.com', 'webpush1.wechat.com'),
    #     ('web2.wechat.com', 'webpush2.wechat.com'),
    #     ('wechat.com', 'webpush.wechat.com'),
    #     ('web1.wechatapp.com', 'webpush1.wechatapp.com'),
    # ]
    # push_uri = base_uri
    # for (searchUrl, pushUrl) in services:
    #     if base_uri.find(searchUrl) >= 0:
    #         push_uri = 'https://%s/cgi-bin/mmwebwx-bin' % pushUrl
    #         break
  elif code == '408':  # 超时
    pass

  return code


def login():
  global skey, wxsid, wxuin, pass_ticket, BaseRequest
  r = s.get(redirect_uri)
  # debugReq(r)
  # print r.text
  data = r.text.encode('utf-8')
  doc = xml.dom.minidom.parseString(data)
  root = doc.documentElement

  for node in root.childNodes:
    if node.nodeName == 'skey':
      skey = node.childNodes[0].data
    elif node.nodeName == 'wxsid':
      wxsid = node.childNodes[0].data
    elif node.nodeName == 'wxuin':
      wxuin = node.childNodes[0].data
    elif node.nodeName == 'pass_ticket':
      pass_ticket = node.childNodes[0].data

  if not all((skey, wxsid, wxuin, pass_ticket)):
    return False

  BaseRequest = {
      'Uin': int(wxuin),
      'Sid': wxsid.encode('unicode_escape'),
      'Skey': skey.encode('unicode_escape'),
      'DeviceID': deviceId,
  }

  return True


def responseState(func, BaseResponse):
  ErrMsg = BaseResponse['ErrMsg']
  Ret = BaseResponse['Ret']
  if Ret != 0:
    print('func: %s, Ret: %d, ErrMsg: %s' % (func, Ret, ErrMsg))

  if Ret != 0:
    return False

  return True


def webwxinit():
  global My, SyncKey

  url = base_uri + "/webwxinit?r=-1746916482&lang=zh_CN&pass_ticket=" + pass_ticket
  payload = {'BaseRequest': BaseRequest}
  headers = {'ContentType': 'application/json; charset=UTF-8'}
  r = s.post(url, json=payload, headers=headers)
  # debugReq(r)
  # print r.text
  data = r.text.encode('unicode_escape').decode('string_escape')
  dic = json.loads(data)
  My = dic['User']
  SyncKey = dic['SyncKey']
  state = responseState('webwxinit', dic['BaseResponse'])
  return state


def webwxsendmsg(friend, content):
  clientMsgId = str(int(time.time()))
  url = base_uri + "/webwxsendmsg?lang=zh_CN&pass_ticket=" + pass_ticket
  Msg = {
      'Type': '1',
      'Content': content,
      'ClientMsgId': clientMsgId.encode('unicode_escape'),
      'FromUserName': My['UserName'].encode('unicode_escape'),
      'ToUserName': friend["UserName"].encode('unicode_escape'),
      'LocalID': clientMsgId.encode('unicode_escape')
  }
  payload = {'BaseRequest': BaseRequest, 'Msg': Msg}
  headers = {'ContentType': 'application/json; charset=UTF-8'}
  # print str(payload).decode('string_escape')
  data = json.dumps(payload, ensure_ascii=False)
  # r = s.post(url, json=payload, headers=headers)
  r = s.post(url, data = data, headers=headers)
  # debugReq(r)
  # print r.text
  resp = json.loads(r.text)
  if 'BaseResponse' in resp:
    if 'Ret' in resp['BaseResponse']:
      return int(resp['BaseResponse']['Ret'])
  return -1

def webwxsync():
  url = base_uri + "/webwxsync?sid=" + wxsid + "&skey=" + skey
  payload = {'BaseRequest': BaseRequest, 'SyncKey': SyncKey, 'rr' : int(time.time())}
  headers = {'ContentType': 'application/json; charset=UTF-8'}
  data = json.dumps(payload, ensure_ascii=False)
  r = s.post(url, data = data, headers=headers)
  # debugReq(r)
  content = r.text.encode('unicode_escape').decode('string_escape')
  resp = json.loads(content)
  return resp

def parseRecvMsgs(msgs):
  mymsgs = []
  m = {}
  for msg in msgs:
    user = findFriend('UserName', msg['FromUserName'])
    if user:
      m[u'FromUserName'] = user['NickName']
    else:
      m[u'FromUserName'] = msg['FromUserName']
    m[u'Content'] = msg['Content']
    m[u'Status'] = msg['Status']

    user = findFriend('UserName', msg['ToUserName'])
    if user:
      m[u'ToUserName'] = user['NickName']
    else:
      m[u'ToUserName'] = msg['ToUserName']
    m[u'MsgType'] = msg['MsgType']
    mymsgs.append(m)
  print json.dumps(mymsgs, ensure_ascii=False)
  return mymsgs

def webwxgetcontact():
  global ContactList
  url = base_uri + "/webwxgetcontact?r=" + str(int(
      time.time()))
  r = s.post(url, json={})
  # debugReq(r)
  content = r.text.encode('unicode_escape').decode('string_escape')
  ContactList = json.loads(content)['MemberList']
  #with open('contacts.txt', 'w') as f:
  #  f.write(content)

def getChatroomList():
  global ChatContactList
  chat_list = []
  for user in ContactList:
    if user['UserName'].find('@@') != -1:  # 群聊
      chat_list.append({"UserName":user['UserName'], "ChatRoomId": ""})

  url = base_uri + "/webwxbatchgetcontact?type=ex&r=%d&lang=zh_CN&pass_ticket=%s"% (time.time(), pass_ticket)
  payload = {
      'BaseRequest': BaseRequest,
      'List': chat_list,
      'Count': len(chat_list)
  }

  r =s.post(url, json=payload)
  data = r.text.encode('unicode_escape').decode('string_escape')
  with open('chatroom.txt', 'w') as f:
    f.write(data)
  ChatContactList = json.loads(data)["ContactList"]

# def webwxbatchgetcontact():
#   url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxbatchgetcontact?type=ex&r=1453704524520"
def findFriend(key, value):
  for friend in ContactList:
    if friend[key] == value:
      # print friend['NickName']
      return friend
  return None

def getRandomMsg():
  lines = open('regards.txt').read().splitlines()
  myline =random.choice(lines)
  return myline

def striphtml(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def main():
  global real_send, http_port
  parser = OptionParser(usage='%prog [options]',
    description='send custom message to your friend on wechat, default dry run')
  parser.add_option('-s', '--sendall',action='store_true', help='send message to your friend, please double check')
  parser.add_option('-p', '--port',type='int', help='http server port listen')

  (options, args) = parser.parse_args()
  if options.sendall:
    real_send = options.sendall
  if options.port:
    http_port = options.port

  server = HTTPServer(('0.0.0.0', http_port), SimpleHTTPRequestHandler)
  thread = threading.Thread(target = server.serve_forever)
  thread.daemon = True
  print "[+] Starting Http Server"
  try:
      thread.start()
  except KeyboardInterrupt:
      server.shutdown()
      sys.exit(0)

  if not getUUID():
    print "[-] UUID get fail"
    return
  print "[+] Getting QR Image..."
  getQRImage()
  while waitForLogin() != '200':
    pass

  if not login():
    print "[-] Login fail"
    return

  print "[+] Login success"

  if not webwxinit():
    print "[-] Wxinit fail"

  webwxgetcontact()

  for f in ContactList:
    name = striphtml(f['RemarkName'].encode('utf-8'))
    if len(name) == 0:
      name = striphtml(f['NickName'].encode('utf-8'))

    # content="嗨, %s 新年快乐 %s" % (name, "[拥抱]")
    content="嗨, %s, %s %s" % (name, getRandomMsg(), "[拥抱]")
    '''
    = -1 : 群聊
    = 0 : 公众号/服务号
    '''
    if f['UserName'].find('@@') != -1 or f['VerifyFlag'] & 8 != 0:
      # content = "skip " + name
      # print "[-] " + content
      # webwxsendmsg(My, content=content)
      continue

    print "[+] Prepare sending to " + name + " ..."
    if webwxsendmsg(My, content=content) != 0:
      print "[!]\tSent to yourself fail, please check your account."
    else:
      print "[*]\tSent to yourself success."


    if real_send:
      # 发给朋友，请检查好喔
      if webwxsendmsg(f, content=content) != 0:
        print "[!]\tSent to " + name + " fail, please check your account."
      else:
        print "[*]\tSent to " + name + " success."

    time.sleep(1)

if __name__ == "__main__":
  main()
