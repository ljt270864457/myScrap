# coding=utf-8

from urllib2 import urlopen
from urllib import urlretrieve
from bs4 import BeautifulSoup
from time import sleep
from urllib2 import HTTPError
import random
import MySQLdb
import re

'''---------------项目需求---------------------
1.采集出北京python职位的要求信息（信息数量不少于300条件）
2.采集出的信息有：a. 薪资b. 公司名称c. 公司地址d. 职位描述
3.把采集到的信息存放到1个txt中，格式不定，但要能够分清楚采集到的不同的职位
'''
# 定义待爬取的url


class GetUrl(object):
    urls1 = []
    urls2 = []

    # 获取1级urls列表
    @classmethod
    def getUrls1(cls):
        for i in range(1, 21):
            url = u'http://www.lagou.com/zhaopin/Python/2/?filterOption=%d' % i
            cls.urls1.append(url.encode('utf-8'))
        print('1级URL列表中共有%d条数据' % len(cls.urls1))
        return cls.urls1

    # 获取二级urls列表
    @classmethod
    def getUrls2(cls):
        if len(cls.urls1) > 0:
            for url1 in cls.urls1:
                soup = Parser.getHTML(url1)
                urls = soup.select('.position_link')
                for i in urls:
                    url = 'http:' + i['href']
                    cls.urls2.append(url)
            print('2级url列表共有%d个url' % len(cls.urls2))
            return cls.urls2
        else:
            print('1级列表为空，不能获取2级列表')
            return None


# 定义一个网页分析类
class Parser(object):
    def __init__(self):
        super(Parser, self).__init__()

    # 判断该URL是否有效,如果正确就返回soup对象
    @staticmethod
    def getHTML(url):
        response = urlopen(url)
        code = response.getcode()
        if code == 200:
            print('(%s)访问成功，ResponseCode is %d' % (url, code))
            soup = BeautifulSoup(response, 'html.parser')
            sleep(random.random())
            return soup
        else:
            print('(%s)访问失败，ResponseCode is %d' % (url, code))
            return None

    # 获取公司名称
    def getName(self, soup):
        name = soup.title.string.encode('utf-8')
        content = re.split('-', name)
        if len(content) > 1:
            result = content[1]
        return result

    # 获取薪资
    def getSalary(self, soup):
        salary = soup.select('.job_request')[0].p.span.string.encode('utf-8')
        return salary

    # 获取公司地址
    def getAddress(self, soup):
        address = soup.select('.work_addr')[0].get_text(
            "", strip=True).encode('utf-8')
        # 去除address中的“-”和空格
        middleAddr = ''.join(address.split('-'))
        finalAddr = ''.join(middleAddr.split())
        return finalAddr

    # 获取职位描述
    def getDesc(self, soup):
        desc = soup.select('.job_bt')[0].get_text(
            "", strip=True).encode('utf-8')
        return desc

# 定义一个job类


class Job(object):
    def __init__(self, name, salary, address, desc):
        self.name = name
        self.salary = salary
        self.address = address
        self.desc = desc

# 定义一个类负责向数据库中插入数据


class InsertData(object):
    def __init__(self):
        super(InsertData, self).__init__()

    @staticmethod
    def myInsert(jobs):
        try:
            # 为了防止插入中文数据乱码，需要在connect函数中增加charset=UTF8
            conn = MySQLdb.connect(host='127.0.0.1', user='root',
                                   passwd='123456', db='Job_Info', port=3306, charset='UTF8')
            cur = conn.cursor()
            conn.select_db('Job_Info')
            cur.executemany("insert into job values(%s,%s,%s,%s,%s)", jobs)
            conn.commit()
            count = cur.execute('select id from job')
            print('插入数据%d条' % count)
            cur.close()
            conn.close()
        except MySQLdb.Error, e:
            print('mysql error %d:%s' % (e.args[0], e.args[1]))

if __name__ == '__main__':
    # 获取1级urls
    urls1 = GetUrl.getUrls1()
    # 获取2级urls，爬虫主要在2级urls进行爬取数据
    urls2 = GetUrl.getUrls2()
    jobs = []
    for url in urls2:
        # 将HTML格式化
        url = url.encode('utf-8')
        soup = Parser.getHTML(url)
        # 爬取的网页列表
        p = Parser()
        # 获取公司名称
        name = p.getName(soup)
        # 获取工资
        salary = p.getSalary(soup)
        # 获取地址
        address = p.getAddress(soup)
        # 获取职位描述
        desc = p.getDesc(soup)
        # 定义一个工作
        job = Job(name, salary, address, desc)
        jobinfo = (0, job.name, job.salary, job.address, job.desc)
        jobs.append(jobinfo)
    # # 去重
    # jobs = list(set(jobs))
    # 向数据库中插入数据
    InsertData.myInsert(jobs)
