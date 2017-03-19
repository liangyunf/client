# encoding: utf-8

import socket
import ssl
import requests
from lxml import html
from utils import log



class Model(object):
    def __repr__(self):
        class_name = self.__class__.__name__
        properties = ('{} = ({})'.format(k, v) for k, v in self.__dict__.items())
        r = '\n<{}:\n  {}\n>'.format(class_name, '\n  '.join(properties))
        return r


class Answer(Model):
    def __init__(self):
        self.author= ''

def parsed_url(url):
    """
    解析 url 返回 (protocol host port path)
    有的时候有的函数, 它本身就美不起来, 你要做的就是老老实实写
    """
    # 检查协议
    protocol = 'http'
    if url[:7] == 'http://':
        u = url.split('://')[1]
    elif url[:8] == 'https://':
        protocol = 'https'
        u = url.split('://')[1]
    else:
        # '://' 定位 然后取第一个 / 的位置来切片
        u = url

    # 检查默认 path
    i = u.find('/')
    if i == -1:
        host = u
        path = '/'
    else:
        host = u[:i]
        path = u[i:]

    # 检查端口
    port_dict = {
        'http': 80,
        'https': 443,
    }
    # 默认端口
    port = port_dict[protocol]
    if host.find(':') != -1:
        h = host.split(':')
        host = h[0]
        port = int(h[1])

    return protocol, host, port, path


def socket_by_protocol(protocol):
    """
    根据协议返回一个 socket 实例
    """
    if protocol == 'http':
        s = socket.socket()
    else:
        # HTTPS 协议需要使用 ssl.wrap_socket 包装一下原始的 socket
        # 除此之外无其他差别
        s = ssl.wrap_socket(socket.socket())
    return s


def response_by_socket(s):
    """
    参数是一个 socket 实例
    返回这个 socket 读取的所有数据
    """
    response = b''
    buffer_size = 1024
    while True:
        r = s.recv(buffer_size)
        if len(r) == 0:
            break
        response += r
    return response


def parsed_response(r):
    """
    把 response 解析出 状态码 headers body 返回
    状态码是 int
    headers 是 dict
    body 是 str
    """
    header, body = r.split('\r\n\r\n', 1)
    h = header.split('\r\n')
    status_code = h[0].split()[1]
    status_code = int(status_code)

    headers = {}
    for line in h[1:]:
        k, v = line.split(': ')
        headers[k] = v
    return status_code, headers, body


# 复杂的逻辑全部封装成函数
def get(url):
    """
    用 GET 请求 url 并返回响应
    """
    protocol, host, port, path = parsed_url(url)

    s = socket_by_protocol(protocol)
    s.connect((host, port))
    #知乎会看请求者的User-agent 以及cokie
    request = 'GET {} HTTP/1.1\r\nhost: {}\r\nUser-Agent:Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36\r\nConnection: close\r\nCookie:d_c0="AFBAHkvEuwqPTvRB29weFlLVw8hP3vkvHsA=|1477179506"; _zap=423de9dd-938c-4301-8808-34d7f32da82a; q_c1=8ee0665f3d6648e6885a6234eca858b1|1488956450000|1477179505000; l_cap_id="OGVkNzVjYTY3NTZmNGYzZWIyNzViOTVhYzFhYjZjMWM=|1489749836|c5cba84087d287ab810c837979b47f5961c7bdf2"; r_cap_id="NmYzNTljMThkMjFmNDMzMzk3MTc4MjI1OGQ2MzdlN2I=|1489749835|5b948739f0887f54fea0ee2e78007883c15ba72d"; cap_id="NGNmNzg0NzM5ZTQyNDNkMmFjOWVhMTk3N2VhMGQ1ODI=|1489749835|3fe3a4b687d7c51843c3dd976a27ca28cf1bb231"; _xsrf=32893ed775ec7ef85c18f07af5e13523; __utma=51854390.745311173.1483324917.1489750002.1489907497.4; __utmb=51854390.0.10.1489907497; __utmc=51854390; __utmz=51854390.1489750002.3.2.utmcsr=baidu|utmccn=(organic)|utmcmd=organic; __utmv=51854390.100--|2=registration_date=20151026=1^3=entry_date=20151026=1; z_c0=Mi4wQUJBS3AwQjg2QWdBVUVBZVM4UzdDaGNBQUFCaEFsVk40VlR6V0FDU00wYU1ma1Ixd0ltQ3BGNkVLSmtyUGllQ2JB|1489907346|20afdf02527b6c8c5a3d3ffee08f9e076c1d1419; nweb_qa=heifetz\r\n\r\n'.format(path, host)
    encoding = 'utf-8'
    s.send(request.encode(encoding))

    response = response_by_socket(s)
    log('response', response)
    r = response.decode(encoding)

    status_code, headers, body = parsed_response(r)
    if status_code == 301:
        url = headers['Location']
        return get(url)
    return status_code, headers, body


def answer_from_div(div):
    a = Answer()
    a.author = div.xpath('.//div[@class=class="UserLink-link"]')[0].text
    return a


def answers_from_url(url):
    _, _, page = get(url)
    root = html.fromstring(page)
    divs = root.xpath('//div[@class="QuestionAnswer-content"]')
    items = [answer_from_div(div) for div in divs]
    return items







def main():
    # 豆瓣电影 top250 爬取不同的页面需要更新url
    url = 'https://www.zhihu.com/question/26791891/answer/38986988'
    answers = answers_from_url(url)
    log('answers', answers)



if __name__ == '__main__':
    main()


