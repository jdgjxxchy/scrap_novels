#!/usr/bin/env python
# encoding: utf-8

"""
@version: 
@author: Wish Chen
@contact: 986859110@qq.com
@file: get_novels.py
@time: 2018/11/21 19:43

"""
import gevent
from gevent import monkey
monkey.patch_all()
import requests, time, random, re, os, sys
from bs4 import BeautifulSoup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
from save_ip import IP_list

dir = os.path.dirname(os.path.abspath(__file__))
personal = ""

def getHTMLText(url, data=[], method='get'):
    """
    获取网站的源代码
    请求默认为get
    :param url:
    :param data:
    :param method:
    :return:
    """
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.81 Safari/537.36"}
    proxies = IP_list().get_random_ip()
    # print(proxies)
    try:
        # print("start", url)
        r = requests.request(method, url, proxies=proxies, headers=headers, data=data)
        r.raise_for_status()
        # r.encoding = r.apparent_encoding
        # print('end', url)
        return r
    except:
        return r.status_code


def fetch_async(x, url):
    """
    异步IO所需要执行的操作
    获取源文件
    模拟向ajax请求获取完整文字
    每一章输入到temp文件夹下
    :param x:
    :param url:
    :return:
    """
    url_main = "http://quanben5.com/index.php?c=book&a=ajax_content"
    r = getHTMLText(url)  # 获取每一章的源文件
    title = re.search(r'<h1 class="title1">(.*)</h1>', r.text).group(1)
    result = re.search(r'<script type="text/javascript">ajax_post\((.*)\)</script>', r.text).group(1)
    num_list = result.split("','")
    num_list[9] = num_list[9][:-1]
    content = {}  # 开始模拟post请求发送的表单
    for i in range(1, 5):
        content[num_list[i * 2]] = num_list[i * 2 + 1]
    content['_type'] = "ajax"
    content['rndval'] = int(time.time() * 1000)
    r = getHTMLText(url_main, data=content, method='post')  # 模拟post请求
    soup = BeautifulSoup(r.text, "lxml")
    with open(os.path.join(dir, 'temp', "%s.txt" % x), "w", encoding='utf8') as f:
        f.writelines(''.join([title, '\n\n', personal, '\n\n']))
        for tag in soup.body.children:
            if tag.name == 'p':
                f.writelines(''.join(['    ', tag.string.strip(), '\n\n']))
    print('%d.%s 下载完成' % (x, title))

def get_together(name, author, x):
    """
    将temp目录下的各网页下载下来的txt
    合并在一起
    并删除temp文件
    :param name:
    :param author:
    :return:
    """
    with open(os.path.join(dir, "%s.txt" % name), "w", encoding='utf8') as f:
        f.writelines(''.join([name, '\n\n作者:', author, '\n\n']))

        for i in range(x):
            try:
                f.write(open(os.path.join(dir, 'temp', "%s.txt" % (i+1)), "r", encoding='utf8').read())
                f.write('\n\n')
                # os.remove(os.path.join(dir, 'temp', "%s.txt" % (i+1)))
            except:
                continue


def parseByQB5(response, host):
    """
    在全本5小说网的源码下爬取小说
    获得书名和作者
    采用gevent异步IO优化
    :param response:
    :param host:
    :return:
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    url_text = soup.find_all('div', 'box')[2]
    main_text = url_text.find_all('h2')[0].next_sibling
    url_list = []
    for tag in main_text.descendants:
        if tag.name == 'li':
            url = ''.join(['http://', host, tag.a.attrs['href']])
            url_list.append(url)
    from gevent.pool import Pool
    pool = Pool(100)

    gevent.joinall([pool.spawn(fetch_async, i+1, url=url_list[i]) for i in range(len(url_list))])

    name = re.search(r"<h3><span>(.*)</span></h3>", response.text).group(1)
    author = re.search(r'<span class="author">(.*)</span></p>', response.text).group(1)
    print("%d文档已下载,正在合并..." % len(url_list))
    get_together(name, author, len(url_list))


def getNovelUrls(url):
    """
    通过小说的目录网址判断小说所在的网站
    并调用属于该网站的爬虫语句
    :param url:
    :return:
    """

    response = getHTMLText(url)
    host = url.split('//')[1].split('/')[0]
    host_list = {
        "quanben5.com": parseByQB5
    }
    host_list[host](response, host)


def get_url():
    input_name = input('>>')
    r = getHTMLText("http://quanben5.com//index.php?c=book&a=search&keywords=%s" % input_name)
    soup = BeautifulSoup(r.text, "html.parser")
    main_book = soup.find_all("div", "pic_txt_list")
    for i in range(len(main_book)):
        tag = main_book[i].h3
        print("%s.%s %s" %(i, tag.span.text, tag.next_sibling.next_sibling.text))
    choice = int(input(">>"))
    if choice in range(len(main_book)):
        return ''.join(["http://quanben5.com", main_book[choice].h3.a["href"], "xiaoshuo.html"])


if __name__ == '__main__':
    # url_list = [
    #     "https://www.qu.la/book/365/",
    #     "https://www.qb5200.tw/xiaoshuo/0/357/",
    #     "http://quanben5.com/n/doupocangqiong/xiaoshuo.html",
    #     "http://quanben5.com/n/dazhuzai/xiaoshuo.html",
    #     "http://quanben5.com/n/douluodalu/xiaoshuo.html",
    #     "http://quanben5.com/n/renxingderuodian/xiaoshuo.html"
    # ]
    if not os.path.exists('temp'):
        os.mkdir('temp')
    while True:
        url = get_url()
        time_start = time.time()
        getNovelUrls(url)
        print("成功爬取! 用时:%ds" % (int((time.time()-time_start)*100)/100))
