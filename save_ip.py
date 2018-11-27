#!/usr/bin/env python
# encoding: utf-8

"""
@version: 
@author: Wish Chen
@contact: 986859110@qq.com
@file: save_ip.py
@time: 2018/11/22 20:04

"""
from gevent import monkey, joinall, spawn
monkey.patch_all()
import random
from bs4 import BeautifulSoup
import requests
import pymysql


class IP_list:


    def __init__(self):
        self.conn = pymysql.connect(host='127.0.0.1', port=3306, user='root',
                               passwd='jdgjxxchy_0820', db='ip_list', charset='utf8')
        self.cursor = self.conn.cursor()
        self.get_ip_list()

    def get_ip_list(self, type='https'):
        # cursor.execute('select ip from iplist where type="%s"' %type)
        self.cursor.execute('select ip from iplist')
        self.ip_list = self.cursor.fetchall()
        self.conn.commit()

    def get_random_ip(self, type="https"):
        random_ip1 = ''.join([type, '://', random.choice(self.ip_list)[0]])
        random_ip2 = ''.join(['http://', random.choice(self.ip_list)[0]])
        # proxy_ip = {type: random_ip1, 'http': random_ip2}
        proxy_ip = {'https': random_ip1}
        return proxy_ip     # 打印出获取到的随机代理IP


    def save_ip_list(self, url='http://www.xicidaili.com/nn/', x=1):
        proxies = self.get_random_ip()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'}
        try:
            response = requests.get(url, headers=headers, proxies=proxies, timeout=2)
        except:
            x += 1
            if x<5:
                self.save_ip_list(url, x)
        # print(response.text)
        obj = BeautifulSoup(response.text, 'html.parser')
        ip_text = obj.findAll('tr', {'class': 'odd'})
        ip_text2 = obj.findAll('tr', {'class': ''})
        x = 0
        for i in range(len(ip_text)):
            try:
                ip_tag = ip_text[i].findAll('td')
                ip_port = ip_tag[1].get_text() + ':' + ip_tag[2].get_text()
                self.cursor.execute('insert ignore into ipList(ip,address,type) values ("%s","%s","%s")' %
                               (ip_port, ip_tag[3].get_text().strip(), ip_tag[5].get_text()))
                x += 1
            except: continue

        for i in range(len(ip_text2)):
            try:
                # print(ip_text2[i])
                ip_tag = ip_text2[i].findAll('td')
                ip_port = ip_tag[1].get_text() + ':' + ip_tag[2].get_text()
                self.cursor.execute('insert ignore into ipList(ip,address,type) values ("%s","%s","%s")' %
                                   (ip_port, ip_tag[3].get_text().strip(), ip_tag[5].get_text()))
                x += 1
            except:continue
        print("共收集到了%s个代理IP" % x)


    def is_alive(self, proxy, type='https'):

        try:
            random_ip1 = ''.join([type, '://', proxy])
            random_ip2 = ''.join(['http://', proxy])
            proxies = {type: random_ip1, 'http': random_ip2}
            requests.get("http://quanben5.com/", proxies=proxies, timeout=10)
            print("success", proxies)
        except:
            self.cursor.execute('insert ignore into ip2List(ip) values ("%s");' % proxy)
            self.cursor.execute('delete from iplist where ip="%s";' % proxy)

    def search_all_ip(self):
        url_list = []
        for i in range(200):
            url_list.append(''.join(["http://www.xicidaili.com/nn/", str(i+1)]))
        print(url_list)
        joinall([spawn(self.save_ip_list, url_list[i], 1) for i in range(len(url_list))])
        self.conn.commit()

    def update_list(self):
        proxies_list = []
        for i in self.ip_list:
            proxies_list.append(i[0])
        joinall([spawn(self.is_alive, proxies_list[i]) for i in range(len(proxies_list))])
        self.conn.commit()


    def close_db(self):
        self.conn.close()


if __name__ == '__main__':
    IP = IP_list()
    # IP.search_all_ip()
    IP.update_list()
    print(IP.ip_list)
    IP.close_db()
