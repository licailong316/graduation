import os
import django

# 设置Dango运行时需要的环境变量DJANGO_SETTINGS_MODULE
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '国家地表水水质数据爬虫及信息管理系统.settings')

# 加载Django的设置
django.setup()
print(os.environ['DJANGO_SETTINGS_MODULE'])

from bs4 import BeautifulSoup
from django.db import transaction
from gp.models import Province
"""完成对省份，城市表的更新"""
province_dict = {}
province = []
province_id = []


html_path = r'D:\source\1.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()
    soup = BeautifulSoup(html_content, 'html.parser')
    """获取省份及城市信息"""
    ul_tag = soup.find('ul', class_='dropdown-menu', attrs={"aria-labelledby": "ddm_Area"})
    for ul_li_tag in ul_tag.children:
        """获取省份名及省份行政代码"""
        a_tag = ul_li_tag.find_next('a')
        onclick_value = a_tag.get('onclick')
        content = onclick_value.split("'")[1:4]
        if content[2].strip() != '城市':
            province_id.append(content[0].strip())
            province.append(content[2].strip())
            province_dict[content[0].strip()] = content[2].strip()

"""填充省份和城市表"""
with transaction.atomic():
    for province_id, province_name in province_dict.items():
        province = Province(province_id=province_id, province_name=province_name)
        province.save()
