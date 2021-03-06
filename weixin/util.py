# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import re

from seats_check.util import * 

test_str_1 = "<xml><ToUserName><![CDATA[ryanc]]></ToUserName><FromUserName><![CDATA[shabi]]></FromUserName><CreateTime>1348831860</CreateTime><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[CS180]]></Content><MsgId>1234567890123456</MsgId></xml>"
test_str = "<xml><ToUserName><![CDATA[ryanc]]></ToUserName><FromUserName><![CDATA[shabi]]></FromUserName><CreateTime>1348831860</CreateTime><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[10001]]></Content><MsgId>1234567890123456</MsgId></xml>"
test_str_2 = "<xml><ToUserName><![CDATA[ryanc]]></ToUserName><FromUserName><![CDATA[shabi]]></FromUserName><CreateTime>1348831860</CreateTime><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[engl106]]></Content><MsgId>1234567890123456</MsgId></xml>"


def parse_xml(in_str, timeout=None):
    root = ET.fromstring(in_str) 
    msg = ''
    content =  root.find('Content').text
    tousername = root.find('FromUserName').text
    fromusername = root.find('ToUserName').text
    createtime = root.find('CreateTime').text
    term = ''
    if not check_mode(content):
        crn = ''
        if len(content) <= 5:
            crn = content.strip()
            term = 'fall2013'
        else:
            crn, term = content.split(' ')
        term_code = convert_term_to_code(term)
        try:
            max_num, curr_num, name, code, number = get_all(crn, term_code)
            rem_num = int(max_num) - int(curr_num)
            msg = '您的课 %s ,课号 %s, Section Number是%s, CRN为%s, 一共有%d个位置, 现在还剩下%d个' % (
                    name.encode('iso-8859-2'), 
                    code.encode('iso-8859-2'),
                    number.encode('iso-8859-2'), 
                    crn.encode('iso-8859-2'), 
                    int(max_num), 
                    int(rem_num)
                    )
        except:
            msg = "Sorry, the CRN %s is not available for term %s" % (crn, term)
    else:
        try:
            result = content.split(' ')
            sub, cnbr = convert_classname(result[0])
        except:
            msg = ('Sorry, the format you use is not correct.\n'
                   'Please see the instruction here:\n'
                   'To check CRN, use "subject"(case insensitive) followed by "class code" without space\n'
                   'Valid format: "CS180", "cs18000"\n\n'
                   'To check seats availability, use 5 digit number\n'
                   'Valid format: "10001"\n\n'
                   'To specify term, append your msg with a space followed by term keyword\n'
                   'Valid format: "cs180 fa13", "cs240 12su"\n\n'
                   'Format of term keyword:\n'
                   'su 2012 / su2012 / 12su => Summer 2012\n'
                   'fa2011 / 11 fa / fa11 => Fall 2011\n\n'
                   'If you have any questions, plz feel free to talk to me\n'
                   'My weixin account: ryancccc\n'
                   'My email: chenrd769@gmail.com\n'
                   )
            re_str = "<xml><ToUserName><![CDATA[%s]]></ToUserName><FromUserName><![CDATA[%s]]></FromUserName><CreateTime>%s</CreateTime><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[%s]]></Content><FuncFlag>0</FuncFlag></xml>" % (tousername, fromusername, createtime, msg)
            return re_str
        sub = sub.upper()
        if len(cnbr) < 5:
            cnbr += '00'
        if len(result) < 2:
            term = 'fall2013'
        else:
            term = result[1]
        term_code = convert_term_to_code(term)
        try:
            if timeout:
                searches = get_all_secs_by_class(sub, cnbr, term_code, timeout)
            else:
                searches = get_all_secs_by_class(sub, cnbr, term_code, 3)
        except ParserException as e:
            msg = e.message
            if 'timed' in e.message:
                msg = 'The content is too large to display!'
            re_str = "<xml><ToUserName><![CDATA[%s]]></ToUserName><FromUserName><![CDATA[%s]]></FromUserName><CreateTime>%s</CreateTime><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[%s]]></Content><FuncFlag>0</FuncFlag></xml>" % (tousername, fromusername, createtime, msg)
            return re_str
        except Exception as e:
            msg = ('Cannot find this class, maybe check your spell and format '
                   'and try again?')
            re_str = "<xml><ToUserName><![CDATA[%s]]></ToUserName><FromUserName><![CDATA[%s]]></FromUserName><CreateTime>%s</CreateTime><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[%s]]></Content><FuncFlag>0</FuncFlag></xml>" % (tousername, fromusername, createtime, msg)
            return re_str
            
        searches = sorted(searches, key = lambda cl: cl['class_time'].start_time)
        msg = '课的名称: \n%s \n有以下这些CRN: \n' % (
            searches[0].get('name').encode('iso-8859-2')
        )

        cur_time = searches[0].get('class_time')
        msg += gen_header(cur_time)
        for cl in searches:
            if cur_time != cl.get('class_time'):
                cur_time = cl.get('class_time')
                msg += gen_header(cur_time)

            msg += '%s | %s | %s\n' % (
                    cl.get('crn').encode('iso-8859-2'),
                    cl.get('number').encode('iso-8859-2'),
                    cl.get('class_type').encode('iso-8859-2')[:3]
                    )
        if len(msg) > 2000:
            msg = msg[:1900] + '\n'
            msg += '对不起，您的返回结果超过2000字，目前无法返回'

    re_str = "<xml><ToUserName><![CDATA[%s]]></ToUserName><FromUserName><![CDATA[%s]]></FromUserName><CreateTime>%s</CreateTime><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[%s]]></Content><FuncFlag>0</FuncFlag></xml>" % (tousername, fromusername, createtime, msg)
    return re_str
         
def check_mode(in_str):
    r = re.compile('^\d{5}$')
    if r.match(in_str):
        return 0
    else:
        return 1

def change_color(in_str, color='#FF1CAE', need=1):
    if need:
        return '<a color=%s>%s</a>' % (color, in_str)
    else:
        return in_str

def gen_header(cur_time):
    msg = ''
    msg += '=' * 18 + '\n' 
    msg += '%s\n' % (
        str(cur_time).encode('iso-8859-2')
    )
    msg += '=' * 18 + '\n'
    msg += ' CRN  | SEC | Type \n'
    return msg

def gen_header_with_color(cur_time):
    msg = ''
    msg += change_color('=' * 18, '#6B238E') + '\n' 
    msg += '%s\n' % (
        change_color(str(cur_time).encode('iso-8859-2'))
    )
    msg += change_color('=' * 18, '#6B238E') + '\n'
    msg += change_color(' CRN  | SEC | Type', '#5C3317') + '\n'
    return msg
