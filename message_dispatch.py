#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#   Author  :   cold
#   E-mail  :   wh_linux@126.com
#   Date    :   13/03/01 11:44:05
#   Desc    :   消息调度
#
from functools import partial

from command import Command
from config import MAX_RECEIVER_LENGTH


code_typs = ['actionscript', 'ada', 'apache', 'bash', 'c', 'c#', 'cpp',
              'css', 'django', 'erlang', 'go', 'html', 'java', 'javascript',
              'jsp', 'lighttpd', 'lua', 'matlab', 'mysql', 'nginx',
              'objectivec', 'perl', 'php', 'python', 'python3', 'ruby',
              'scheme', 'smalltalk', 'smarty', 'sql', 'sqlite3', 'squid',
              'tcl', 'text', 'vb.net', 'vim', 'xml', 'yaml']

ABOUT_STR = u"Author    :   cold\nE-mail    :   wh_linux@126.com\n"\
        u"HomePage  :   http://www.linuxzen.com\n"\
        u"Project@  :   https://github.com/coldnight/pual_bot"

class MessageDispatch(object):
    """ 消息调度器 """
    def __init__(self, webqq):
        self.webqq = webqq
        self.cmd = Command()

    def send_msg(self, content, callback, nick = None):
        self.cmd.send_msg(content, callback, nick)

    def handle_qq_msg_contents(self, contents):
        content = ""
        for row in contents:
            if isinstance(row, (str, unicode)):
                content += row.replace(u"【提示：此用户正在使用Q+"
                                       u" Web：http://web.qq.com/】", "")\
                        .replace(u"【提示：此用户正在使用Q+"
                                       u" Web：http://web3.qq.com/】", "")
        return  content.replace("\r", "\n").replace("\r\n", "\n")\
                .replace("\n\n", "\n")


    def handle_qq_group_msg(self, message):
        """ 处理组消息 """
        value = message.get("value", {})
        gcode = value.get("group_code")
        uin = value.get("send_uin")
        contents = value.get("content", [])
        content = self.handle_qq_msg_contents(contents)
        uname = self.webqq.get_group_member_nick(gcode, uin)
        if content:
            pre = u"{0}: ".format(uname)
            callback = partial(self.webqq.send_group_msg, gcode)
            self.handle_content(content, callback, pre)


    def handle_qq_message(self, message):
        """ 处理QQ好友消息 """
        value = message.get("value", {})
        from_uin = value.get("from_uin")
        contents = value.get("content", [])
        content = self.handle_qq_msg_contents(contents)
        if content:
            callback = partial(self.webqq.send_buddy_msg, from_uin)
            self.handle_content(content, callback)

    def handle_content(self, content, callback, pre = None):
        """ 处理内容
        Arguments:
            `content`   -       内容
            `callback`  -       仅仅接受内容参数的回调
            `pre`       -       处理后内容前缀
        """
        send_msg = partial(self.send_msg, callback = callback, nick = pre)
        if content.startswith("-py"):
            body = content.lstrip("-py").strip()
            self.cmd.py(body, send_msg)

        if content.startswith("```"):
            typ = content.split("\n")[0].lstrip("`").strip().lower()
            if typ not in code_typs: typ = "text"
            code = "\n".join(content.split("\n")[1:])
            self.cmd.paste(code, send_msg, typ)

        if content.strip() == "ping " + self.webqq.nickname:
            body = u"I am here ^ ^"
            send_msg(body)

        if content.strip() == "about " + self.webqq.nickname:
            body = ABOUT_STR
            send_msg(body)

        if content.strip() == "uptime " + self.webqq.nickname:
            body = self.webqq.get_uptime()
            send_msg(body)

        if content.startswith("-tr"):
            if content.startswith("-trw"):
                web = True
                st = "-trw"
            else:
                web = False
                st = "-tr"
            body = content.lstrip(st).strip()
            self.cmd.cetr(body, send_msg, web)

        if len(content) > MAX_RECEIVER_LENGTH:
            if pre:
                cpre = u"{0}内容过长: ".format(pre)
            else:
                cpre = pre
            send_pre_msg = partial(self.send_msg, callback = callback, nick = cpre)
            self.cmd.paste(content, send_pre_msg)


    def dispatch(self, qq_source):
        if qq_source.get("retcode") == 0:
            messages = qq_source.get("result")
            for m in messages:
                if m.get("poll_type") == "group_message":
                    self.handle_qq_group_msg(m)
                if m.get("poll_type") == "message":
                    self.handle_qq_message(m)