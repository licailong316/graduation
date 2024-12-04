import os
import csv
import time
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup
from django.db import transaction
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from gp.models import Data, Province, City, Basin, River, Section

'''
将此爬虫函数用于后台页面的数据爬取时，初次设定的等待时间不能过长，
应该将等待时间设为变量，使用超时异常捕捉，当初次爬取数据失败后增加等待刷新时间，再次爬取
循环往复，直至数据爬取成功。

设想
将数据的相关操作实现为几个函数
crawler_source_code() 爬取html源代码，返回值为源码
extract_date() 从爬取的HTML源代码中提取数据 返回值为提取后的数据
data_process() 处理提取后的数据，将缺失值补齐
save_to_mysql() 先连接数据库，然后对处理后的每一条数据，先检索其是否在数据库中；若不在数据库中将该条数据存储到数据库中，否则将该条数据舍弃
show_data() 返回此次数据爬取获取的新数据（不在数据库中的数据），若本次爬取数据全部在数据库中则返回提示消息，否则返回数据和提示信息
process_csv() 处理已经存在的csv数据文件
evaluate_water_quality() 水质数据评估，对于水质类别确实的数据，通过现有的其他水质影响因素判断水质类别，将判断后的水质类别补充到挡前数据中，对无法判断的给出特殊标记
water_quality_type() 根据提取的数据返回数据类型
handle_date() 对缺少日期的数据进行处理
'''

def crawler_source_code():
    # 创建Chrome浏览器的选项对象
    chrome_options = Options()
    # 设置Chrome浏览器为无头模式
    chrome_options.add_argument("--headless")
    # 解决DevToolsActivePort文件不存在的报错
    chrome_options.add_argument("--no-sandbox")
    # 禁用GPU加速
    chrome_options.add_argument("--disable-gpu")
    # 初始化Chrome浏览器，传入chrome_options参数
    driver = webdriver.Chrome(options=chrome_options)
    # 打开网页
    driver.get("https://szzdjc.cnemc.cn:8070/GJZ/Business/Publish/RealDatas.html")
    wait = WebDriverWait(driver, 5)

    # 等待城市按钮可点击并点击
    city_button = wait.until(EC.element_to_be_clickable((By.ID, 'ddm_Area')))
    city_button.click()

    # 选择“全国”
    national_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[text()="全国"]')))
    national_option.click()
    time.sleep(5)

    # 设置每次按键的滚动距离
    scroll_step = 500
    scroll_position = 0

    # 执行键盘按键模拟滚动
    while scroll_position < driver.execute_script("return document.body.scrollHeight"):
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.PAGE_DOWN)  # 模拟按下 “Page Down” 键
        time.sleep(0.1)  # 等待滚动加载
        scroll_position += scroll_step
    # time.sleep(3)

    # 等待动态内容加载完成
    wait.until(EC.presence_of_element_located((By.ID, 'gridDatas')))

    # 获取页面源码
    page_source = driver.page_source

    # 关闭浏览器
    driver.quit()
    # 返回HTML源码
    return page_source


def extract_date(page_source):
    total_data = []
    header = []
    html_content = page_source
    soup = BeautifulSoup(html_content, 'html.parser')

    """该部分的主要作用是从HTML源码中提取表头，并将数据存储到header列表中"""
    table_tag = soup.find('table', id="gridHd")
    if table_tag:
        table_tr_tag = table_tag.find('tr')
        for table_tr_td_tag in table_tr_tag.find_all('td'):
            header.append(table_tr_td_tag.text.strip())
        header.insert(2, '所属地区')
        header.insert(3, '所属河流')

    """该部分的主要作用是从HTML源码中获取表数据，并将获取的数据存储到total_data列表"""
    ul_tag = soup.find('ul', id='gridDatas')
    if ul_tag:
        for li_tag in ul_tag.find_all('li', class_='news-item'):  # 遍历所有li标签
            data = []
            tr_tag = li_tag.find('tr')
            if tr_tag:
                for td_tag in tr_tag.find_all('td'):
                    span_tag = td_tag.find('span')
                    if span_tag:
                        if span_tag.find():
                            str1 = span_tag.find().get('data-original-title')
                            if str1:
                                lines = str1.split('\n')
                                for line in lines:
                                    colon_index = line.find(':')
                                    if colon_index != -1:
                                        value = line[colon_index + 1:].strip()
                                        data.append(value)
                        span_text = span_tag.text
                        data.append(span_text)
                    else:
                        td_text = td_tag.text
                        data.append(td_text)
            total_data.append(data)

    # 返回从HTML源码中提取到的数据
    return header, total_data


def water_quality_type(new_data):
    data = [0 if value in ['--', '', '*'] else float(value) for value in new_data]
    ph_value, do_value, cod_value, tn_value, tp_value = data
    if 6 < ph_value < 9:
        if do_value >= 7.5 and cod_value <= 2 and tn_value <= 0.15 and tp_value <= 0.02:
            return 'Ⅰ'
        elif do_value >= 6 and cod_value <= 4 and tn_value <= 0.5 and tp_value <= 0.1:
            return 'Ⅱ'
        elif do_value >= 5 and cod_value <= 6 and tn_value <= 1 and tp_value <= 0.2:
            return 'Ⅲ'
        elif do_value >= 3 and cod_value <= 10 and tn_value <= 1.5 and tp_value <= 0.3:
            return 'Ⅳ'
        elif do_value >= 2 and cod_value <= 15 and tn_value <= 2 and tp_value <= 0.4:
            return 'Ⅴ'
        else:
            return '劣Ⅴ'
    else:
        return '劣Ⅴ'


def evaluate_water_quality(total_data):
    """
    获取用户水质评价的5项指标pH、溶解氧、高锰酸盐指数、氨氮、总磷,对水质类型缺失的数据进行处理
    """
    index = [8, 9, 12, 13, 14]
    for i in range(len(total_data)):
        if total_data[i][6] not in ['Ⅰ', 'Ⅱ', 'Ⅲ', 'Ⅳ', 'Ⅴ', '劣Ⅴ']:
            new_data = [total_data[i][j] for j in index]
            water_type = water_quality_type(new_data)
            total_data[i][6] = water_type


def handle_date(total_data):
    data = total_data
    for i in range(len(data)):
        if data[i][5] in ['\xa0', '', '--', '*']:
            try:
                if data[i + 1][5] in ['\xa0', '', '--', '*']:
                    data[i][5] = data[i - 1][5]
                else:
                    data[i][5] = data[i + 1][5]
            except IndexError:
                # 如果发生索引超出范围，则使用上一个记录的值
                data[i][5] = data[i - 1][5]


def handle_missing_data(total_data):
    for i in range(len(total_data)):
        for j in range(len(total_data[i])):
            if total_data[i][j] in ['\xa0', '', '--', '*']:
                total_data[i][j] = -1
    # return total_data


def data_process():
    header, total_data = extract_date()
    evaluate_water_quality(total_data)
    handle_date(total_data)
    handle_missing_data(total_data)


def check_record_in_database(record):
    # print("记录1：", record)
    try:
        # print("记录2：", record)
        data_object = Data.objects.get(
            province__province_name=record[1],
            city__city_name=record[2],
            basin__basin_name=record[3],
            river__river_name=record[4],
            section__section_name=record[5],
            monitoring_time=datetime.strptime(str(record[5]), '%m-%d %H:%M')
        )
        # print("记录3：", record)
        return True  # 数据在数据库中
    except Data.DoesNotExist:
        # print("记录4：", record)
        return False  # 数据不在数据库中
    except Exception as e:
        # print(f"记录5：发生了其他异常 {record}，异常信息：{e}")
        return True  # 发生其他异常时返回True


def save_to_mysql(data_list):
    # 接收数据列表
    data_list1 = data_list
    for record in data_list1:
        True_or_False = check_record_in_database(record)
        # print(True_or_False)
        if not True_or_False:
            try:
                with transaction.atomic():
                    pd_obj = Province.objects.filter(province_name=record[0]).first()
                    cd_obj = City.objects.filter(city_name=record[2]).first()
                    bd_obj = Basin.objects.filter(basin_name=record[1]).first()
                    rd_obj = River.objects.filter(river_name=record[3]).first()
                    sd_obj = Section.objects.filter(section_name=record[4]).first()
                    if pd_obj and bd_obj and cd_obj and rd_obj and sd_obj:
                        data1 = Data(
                            province=pd_obj,
                            city=cd_obj,
                            basin=bd_obj,
                            river=rd_obj,
                            section=sd_obj,
                            monitoring_time=parser.parse(record[5]) if record[5] not in ['*', '\xa0', '',
                                                                                         '--'] else None,
                            water_type=record[6] if record[6] not in ['*', '\xa0', '', '--'] else None,
                            water_temperature=float(record[7]) if record[7] not in ['*', '\xa0', '',
                                                                                    '--'] else None,
                            pH=float(record[8]) if record[8] not in ['*', '\xa0', '', '--'] else None,
                            dissolved_oxygen=float(record[9]) if record[9] not in ['*', '\xa0', '', '--'] else None,
                            conductivity=float(record[10]) if record[10] not in ['*', '\xa0', '', '--'] else None,
                            turbidity=float(record[11]) if record[11] not in ['*', '\xa0', '', '--'] else None,
                            permanganate_index=float(record[12]) if record[12] not in ['*', '\xa0', '',
                                                                                       '--'] else None,
                            ammonia_nitrogen=float(record[13]) if record[13] not in ['*', '\xa0', '',
                                                                                     '--'] else None,
                            total_phosphorus=float(record[14]) if record[14] not in ['*', '\xa0', '',
                                                                                     '--'] else None,
                            total_nitrogen=float(record[15]) if record[15] not in ['*', '\xa0', '', '--'] else None,
                            chlorophyll_alpha=float(record[16]) if record[16] not in ['*', '\xa0', '',
                                                                                      '--'] else None,
                            algal_density=float(record[17]) if record[17] not in ['*', '\xa0', '', '--'] else None,
                            station_status=record[18]
                        )
                        data1.save()
                        # saved_data1 = data1.save()  # 尝试保存数据，并获取返回的对象实例
                        # # print(bool(saved_data1))
                        # if not saved_data1:
                        #     print("Data saved successfully!")
                        # else:
                        #     print("Data save failed.")
            except Exception as e:
                pass


# def crawler():
#     # 创建Chrome浏览器的选项对象
#     chrome_options = Options()
#
#     # 设置Chrome浏览器为无头模式
#     chrome_options.add_argument("--headless")
#     chrome_options.add_argument("--no-sandbox")  # 解决DevToolsActivePort文件不存在的报错
#     chrome_options.add_argument("--disable-gpu")  # 禁用GPU加速
#
#     # 指定文件存储目录
#     directory = r'D:\Python\source\source_html'
#     directory_csv = r'D:\Python\source\source_csv'
#
#     # 确保目录存在，如果不存在则创建目录
#     if not os.path.exists(directory):
#         os.makedirs(directory)
#
#     if not os.path.exists(directory_csv):
#         os.makedirs(directory_csv)
#
#     crawl_count = 1
#
#     total_data = []
#     header = []
#     # 初始化Chrome浏览器，传入chrome_options参数
#     driver = webdriver.Chrome(options=chrome_options)
#     # 打开网页
#     driver.get("https://szzdjc.cnemc.cn:8070/GJZ/Business/Publish/RealDatas.html")
#     wait = WebDriverWait(driver, 10)
#
#     # 等待城市按钮可点击并点击
#     city_button = wait.until(EC.element_to_be_clickable((By.ID, 'ddm_Area')))
#     city_button.click()
#
#     # 选择“全国”
#     national_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[text()="全国"]')))
#     national_option.click()
#     time.sleep(10)
#
#     # 设置每次按键的滚动距离
#     scroll_step = 500
#     scroll_position = 0
#
#     # 执行键盘按键模拟滚动
#     while scroll_position < driver.execute_script("return document.body.scrollHeight"):
#         body = driver.find_element(By.TAG_NAME, "body")
#         body.send_keys(Keys.PAGE_DOWN)  # 模拟按下 “Page Down” 键
#         time.sleep(0.5)  # 等待滚动加载
#         scroll_position += scroll_step
#     time.sleep(5)
#
#     # 等待动态内容加载完成
#     wait.until(EC.presence_of_element_located((By.ID, 'gridDatas')))
#
#     # 获取页面源码
#     page_source = driver.page_source
#     file_name = os.path.join(directory, f"{crawl_count}.html")
#     with open(file_name, "w", encoding='utf-8') as file:
#         file.write(page_source)
#     print(f"第{crawl_count}次爬取数据已保存到文件: {file_name}")
#     with open(file_name, "r", encoding='utf-8') as f:
#         html_content = f.read()
#         soup = BeautifulSoup(html_content, 'html.parser')
#         table_tag = soup.find('table', id="gridHd")
#         if table_tag:
#             table_tr_tag = table_tag.find('tr')
#             for table_tr_td_tag in table_tr_tag.find_all('td'):
#                 header.append(table_tr_td_tag.text.strip())
#             header.insert(2, '所属地区')
#             header.insert(3, '所属河流')
#         ul_tag = soup.find('ul', id='gridDatas')
#         if ul_tag:
#             for li_tag in ul_tag.find_all('li', class_='news-item'):  # 遍历所有li标签
#                 data = []
#                 tr_tag = li_tag.find('tr')
#                 if tr_tag:
#                     for td_tag in tr_tag.find_all('td'):
#                         span_tag = td_tag.find('span')
#                         if span_tag:
#                             if span_tag.find():
#                                 str1 = span_tag.find().get('data-original-title')
#                                 lines = str1.split('\n')
#                                 for line in lines:
#                                     colon_index = line.find(':')
#                                     if colon_index != -1:
#                                         value = line[colon_index + 1:].strip()
#                                         data.append(value)
#                             span_text = span_tag.text
#                             data.append(span_text)
#                         else:
#                             td_text = td_tag.text
#                             data.append(td_text)
#                 total_data.append(data)
#     file_path = os.path.join(directory_csv, f'{crawl_count}.csv')
#     with open(file_path, 'w', newline='', encoding='utf-8') as f2:
#         writer = csv.writer(f2)
#         writer.writerow(header)
#         writer.writerows(total_data)
#     print('数据已成功写入CSV文件:', file_path)
#
#     # 关闭浏览器
#     driver.quit()
#
#     # # 增加爬取次数
#     # crawl_count += 1
#     #
#     # # 等待1小时再次爬取
#     # time.sleep(3600)  # 3600秒 = 1小时
#
#
# # def data_process():
# #     df = crawler()


"""
在后台管理的数据爬取菜单下添加一个菜单选项，在该选项页面中添加一个表单，用于选择一个数据文件，接收数据文件后将文件传递到后端
在后端对数据文件进行处理，将处理后的数据存储到数据库中。

4/21/21:24
新想法 将爬取数据相关的操作做成一个大的菜单选项，里面包括数据实时爬取、数据处理（上传源文件进行处理并储存到数据库中）、数据导出（实现数据多种格式的导出、特定数据的导出、全部数据的导出、根据时间范围进行数据的导出、按地点进行数据的导出）
、数据统计（统计水质数据在一段时间内各个指标的最值、均值；统计某一断面在一段时间内水质数据各个指标的最值均值）
"""
