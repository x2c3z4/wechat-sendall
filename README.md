# wechat-sendall
过年了，给好友群发微信祝福过年吧，加上好友的名字，诚意十足，居家必备。

主要代码借鉴https://github.com/0x5e/wechat-deleted-friends。
感谢。

# 效果图
![](wechat.gif)

# 使用
```
 $ python mychat.py
[+] get QR Image...
[+] Open http://192.168.1.117/qrcode.jpg
[+] 成功扫描,请在手机上点击确认以登录
[+] 正在登录...
[+] Login success
```
默认将登录二维码放在/var/www/html，没有apache可以直接进入目录打开二维码，扫描登录。

*注意*
```
373 webwxsendmsg(f, content=content)
```
默认注释掉373行，打开了就给好友发祝福了，同时也给自己发一遍。
确认发给自己没问题了，再发出去噢。。。。要不闹笑话了。

*注意2*
记得提前备注好好友的名字，没有备注的话使用昵称。

# 测试
目前只在mac上测试，欢迎修改。

