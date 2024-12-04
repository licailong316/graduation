import os
import csv
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
    print(chrome_options)
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


if __name__ == '__main__':
    page_source = crawler_source_code()
    header, total_data = extract_date(page_source)

    # 定义存储路径
    save_dir = 'E:/csv/'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # 定义文件名
    file_name = 'data.csv'
    file_path = os.path.join(save_dir, file_name)

    # 将数据写入 CSV 文件
    with open(file_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        # 写入表头
        writer.writerow(header)
        # 写入数据
        writer.writerows(total_data)

    print(f"CSV 文件已保存到：{file_path}")
