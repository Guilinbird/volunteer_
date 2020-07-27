"""
@Author  :   xiyu
@File    :   volunteer_spider.py
@Time    :   2020/7/25/14:34
@Desc    :
"""

import time
import json

import requests
from lxml import etree


OUTPUT_FILE_PATH = r'D:\volunteer_.json'


class VolunteerAnalysis(object):

    def __init__(self, province, level="高职高专", url_prefix=("http://www.bk179.com", "/volunteer/school")):
        """
        :param province: 省份：湖北省、广东省
        :param level: 学历：高职高专 or 普通本科 or ""
        :param url_prefix: url前缀
        """
        self.province = province
        self.level = level
        self.url_prefix = url_prefix

        self.data = {province: {level: {}}}
        self.time_out_limit = 0
        self.mark_request_end_time = 0.0
        self.total_count = 0
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"}

    def get_response_data(self, url):
        """  获取相应数据，添加请求时间间隔 """
        if time.time() - self.mark_request_end_time < self.time_out_limit:
            time.sleep(self.time_out_limit)
        response = requests.get(url, headers=self.headers)
        self.mark_request_end_time = time.time()
        return response

    def get_page_url_from_start_url(self, start_url):
        """  获取每一页的url """
        page_info_response = self.get_response_data(start_url)
        total_num = 1
        if page_info_response:
            page_info_content = etree.HTML(page_info_response.content.decode())
            page_total_num = page_info_content.xpath("//div[@class='page-devide']/div/a[@class='end']")
            page_show_num = page_info_content.xpath("//div[@class='page-devide']/div/a[@class='num']")
            total_num = page_total_num.text() if page_total_num else len(page_show_num)+1
        self.get_school_per_page(total_num)

    def get_school_per_page(self, total_num):
        """  获取每页中学校列表 """
        for page_num in range(1, total_num+1):
            request_url = ''.join(self.url_prefix) + "/region/" + self.province + "/level/" + \
                          self.level + "/p/" + str(page_num) + ".html"
            response = self.get_response_data(request_url)
            if response:
                content = etree.HTML(response.content.decode())
                for item in content.xpath("//div[@class='major_school_list clearfix']"):
                    detail_url = self.url_prefix[0] + item.xpath("./div[@class='left fl']/a/@href")[0]
                    name = item.xpath("./div[@class='schoollist fl']/div[@class='school-header']/div[@class='school-name']/text()")[0]
                    attr = item.xpath("./div[@class='schoollist fl']/div[@class='school-header']/div[@class='school-attr']/text()")
                    advantage = item.xpath("./div[@class='schoollist fl']/div[@class='school-youshi']/ol/li/a/text()")
                    area, detail_info = self.get_major_per_school(detail_url.replace("schooldata", "schoolmajor"))
                    print(self.total_count, name, "完成")
                    school_inner_info = dict(标签=attr, 优势专业=advantage)
                    school_inner_info.update(detail_info)
                    school_info = {name: school_inner_info}
                    if self.data[self.province][self.level].get(area):
                        self.data[self.province][self.level][area].update(school_info)
                    else:
                        self.data[self.province][self.level].update({area: school_info})
                    self.total_count += 1

    def get_major_per_school(self, school_url):
        """  获取每个学校的信息、专业列表 """
        school_response = self.get_response_data(school_url)
        if school_response:
            major_dict = {}
            content = etree.HTML(school_response.content.decode())
            addr_title = content.xpath("//div[@class='major_tit1']/div/div[4]/div[1]/div[1]/text()")[0]
            addr_info = content.xpath("//div[@class='major_tit1']/div/div[4]/div[1]/div[2]/text()")
            addr_info = addr_info[0] if addr_info else None
            off_website_title = content.xpath("//div[@class='major_tit1']/div/div[5]/div[1]/div[1]/text()")[0]
            off_website_info = content.xpath("//div[@class='major_tit1']/div/div[5]/div[1]/div[2]/text()")
            off_website_info = off_website_info[0] if off_website_info else None
            zs_website_title = content.xpath("//div[@class='major_tit1']/div/div[5]/div[2]/div[1]/text()")[0]
            zs_website_info = content.xpath("//div[@class='major_tit1']/div/div[5]/div[2]/div[2]/text()")
            zs_website_info = zs_website_info[0] if zs_website_info else None
            for detail_major in content.xpath("//div[@class='forlabel']"):
                major_dict.update({detail_major.xpath("./h6/text()")[0]:
                                       dict(zip(detail_major.xpath("./ol/li/a/text()"), [self.url_prefix[0]+x for x in detail_major.xpath("./ol/li/a/@href")]))})
            if not addr_info or addr_info.find("武汉") == -1:
                return "非武汉", {addr_title: addr_info, off_website_title: off_website_info,
                                zs_website_title: zs_website_info, "专业列表": major_dict}
            return "武汉", {addr_title: addr_info, off_website_title: off_website_info,
                            zs_website_title: zs_website_info, "专业列表": major_dict}

    def get_major_info(self):
        """  获取每个学校每个专业的信息：名称、招生人数、主学科目、就业方向、百度百科的描述 """
        pass

    def save_school_major_info(self):
        """  将数据保存成csv格式 """
        with open(OUTPUT_FILE_PATH, 'w', encoding='utf-8') as fw:
            fw.write(json.dumps(self.data, ensure_ascii=False).replace("\\r\\n", ""))

    def load_saved_data(self):
        """  将原有数据进行缓存 """
        with open(OUTPUT_FILE_PATH, 'r', encoding='utf-8') as fr:
            self.data.update(json.loads(fr.read()))

    def run(self, start_url):
        """ 程序入口 """
        self.load_saved_data()
        self.get_page_url_from_start_url(start_url)
        self.save_school_major_info()


class MajorInfoCollector(object):

    def __init__(self, wiki_list):
        wiki_list = []

    def get_search_info(self):
        """  遍历查询百科信息，筛选出关键词 """
        pass


if __name__ == '__main__':
    spider = VolunteerAnalysis("湖北省")
    spider.run("http://www.bk179.com/Volunteer/school.html?region=%E6%B9%96%E5%8C%97%E7%9C%81&level=%E9%AB%98%E8%81%8C%E9%AB%98%E4%B8%93")
