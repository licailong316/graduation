import os
import django

# 设置Dango运行时需要的环境变量DJANGO_SETTINGS_MODULE
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '国家地表水水质数据爬虫及信息管理系统.settings')

# 加载Django的设置
django.setup()
print(os.environ['DJANGO_SETTINGS_MODULE'])
from dateutil import parser
from bs4 import BeautifulSoup
from django.db import transaction
from gp.models import Province, City, Basin, River, Data, Section

"""完成对省份，城市表的更新"""
# 用于填充province表
province_dict = {}
# 用于填充city表
city_dict = {}
# 用于判断city是否完整
city = []
province = []
province_id = []
city_id = []
province_city = {}
# 填充basin表
basin = []
# 填充river表
river = []
basin_river = []
# 填充section表
section = []
# 填充数据表
total_data = []
s_city = []
s_river = []
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
        """获取城市名及城市行政代码"""
        ul_li_ul_tag = ul_li_tag.find_next('ul')
        if ul_li_ul_tag:
            for ul_li_ul_li_tag in ul_li_ul_tag.children:
                ul_li_ul_li_li_a_tag = ul_li_ul_li_tag.find_next('a')
                content1 = ul_li_ul_li_li_a_tag.get('onclick').split("'")[1:4]
                city_id.append(content1[0].strip())
                city.append(content1[2].strip())
                city_dict[content1[0].strip()] = content1[2].strip()
    """获取流域信息"""
    basin_ul_tag = soup.find('ul', class_='dropdown-menu', attrs={"aria-labelledby": "ddm_River"})
    for basin_ul_li_tag in basin_ul_tag.children:
        basin_ul_li_a_tag = basin_ul_li_tag.find_next('a')
        content2 = basin_ul_li_a_tag.text.strip()
        if content2 != '所有流域':
            basin.append(content2)
    """获取数据信息"""
    s_ul_tag = soup.find('ul', id='gridDatas')
    for s_li_tag in s_ul_tag.find_all('li', class_='news-item'):
        tr_tag = s_li_tag.find_next('tr')
        data = []
        if tr_tag:
            td_mn_tag = tr_tag.find('td', class_='MN')
            td_mn_span = td_mn_tag.find('span')
            str1 = td_mn_span.find().get('data-original-title')
            lines = str1.split('\n')
            s_city.append(lines[0][lines[0].find(':') + 1:].strip())
            s_river.append(lines[1][lines[1].find(':') + 1:].strip())
            for td_tag in tr_tag.find_all('td'):
                span_tag = td_tag.find('span')
                if span_tag:
                    span_text = span_tag.text
                    data.append(span_text)
                else:
                    td_text = td_tag.text
                    data.append(td_text)
            data.insert(2, lines[0][lines[0].find(':') + 1:].strip())
            data.insert(3, lines[1][lines[1].find(':') + 1:].strip())
        total_data.append(data)


city_dict['110112'] = '通州区'
city_dict['500111'] = '大足区'
city_dict['500119'] = '南川区'
city_dict['500154'] = '开州区'
city_dict['500240'] = '石柱土家族自治县'
city_dict['513300'] = '甘孜藏族自治州'
city_dict['530000'] = '上海市'

for data_list in total_data:
    cityProvince = data_list[0].strip()
    cname = data_list[2].strip()
    for cityId, cityName in city_dict.items():
        if cityName == cname:
            province_city[cityId] = [cityProvince, cityName]
            break
    if [data_list[1], data_list[3]] not in basin_river:
        basin_river.append([data_list[1], data_list[3]])
    if data_list[3] not in river:
        river.append(data_list[3])
    if [data_list[0],data_list[1],data_list[2],data_list[3],data_list[4]] not in section:
        section.append([data_list[0],data_list[1],data_list[2],data_list[3],data_list[4]])
    print(data_list)

"""填充省份和城市表  已修改无误"""
with transaction.atomic():
    # for province_id, province_name in province_dict.items():
    #     province = Province(province_id=province_id, province_name=province_name)
    #     province.save()

    for city_id1, city_info in province_city.items():
        province_name, city_name = city_info
        province_obj = Province.objects.filter(province_name=province_name).first()
        if province_obj:
            # 创建 City 对象并指定外键字段 province
            city1 = City(city_id=city_id1, city_name=city_name, province=province_obj)
            city1.save()
        else:
            print(f"未找到省份名称为'{province_name}'的省份信息，无法创建城市对象")



"""填充流域和河流表 这里的流域-河流应该用集合而不是列表，确保唯一性 已修改确保无误"""
with transaction.atomic():
    # for j in basin:
    #     basin1 = Basin(basin_name=j)
    #     basin1.save()
    for i in basin_river:
        basinName, riverName = i
        basin_obj = Basin.objects.filter(basin_name=basinName).first()
        if basin_obj:
            river1 = River(river_name=riverName, basin=basin_obj)
            river1.save()
        else:
            print(f"未找到流域名称为'{basinName}'的流域信息，无法创建河流对象")

for m in basin_river:
    if m[1] not in river:
        print(m[1])
        river.append(m[1])
print(basin_river)
print(len(basin_river))
print(river)
print(len(river))


"""填充断面表 已修改无误"""
with transaction.atomic():
    for k in section:
        pn, bn, cn, rn, sn = k
        p_obj = Province.objects.filter(province_name=pn).first()
        b_obj = Basin.objects.filter(basin_name=bn).first()
        c_obj = City.objects.filter(city_name=cn).first()
        r_obj = River.objects.filter(river_name=rn).first()
        if p_obj and b_obj and c_obj and r_obj:
            section1 = Section(province=p_obj, city=c_obj, basin=b_obj, river=r_obj, section_name=sn)
            section1.save()
        else:
            print(f"未找到相关信息，无法创建断面对象")



"""填充数据表"""
with transaction.atomic():
    for data_list1 in total_data:
        pd_obj = Province.objects.filter(province_name=data_list1[0]).first()
        cd_obj = City.objects.filter(city_name=data_list1[2]).first()
        bd_obj = Basin.objects.filter(basin_name=data_list1[1]).first()
        rd_obj = River.objects.filter(river_name=data_list1[3]).first()
        sd_obj = Section.objects.filter(section_name=data_list1[4]).first()
        if pd_obj and bd_obj and cd_obj and rd_obj and sd_obj:
            data1 = Data(province=pd_obj,
                         city=cd_obj,
                         basin=bd_obj,
                         river=rd_obj,
                         section=sd_obj,
                         monitoring_time=parser.parse(data_list1[5]) if data_list1[5] not in ['*', '\xa0', '', '--'] else None ,
                         water_type=data_list1[6] if data_list1[6] not in ['*', '\xa0', '', '--'] else None,
                         water_temperature=float(data_list1[7]) if data_list1[7] not in ['*', '\xa0', '', '--'] else None,
                         pH=float(data_list1[8]) if data_list1[8] not in ['*', '\xa0', '', '--'] else None,
                         dissolved_oxygen=float(data_list1[9]) if data_list1[9] not in ['*', '\xa0', '', '--'] else None,
                         conductivity=float(data_list1[10]) if data_list1[10] not in ['*', '\xa0', '', '--'] else None,
                         turbidity=float(data_list1[11]) if data_list1[11] not in ['*', '\xa0', '', '--'] else None,
                         permanganate_index=float(data_list1[12]) if data_list1[12] not in ['*', '\xa0', '', '--'] else None,
                         ammonia_nitrogen=float(data_list1[13]) if data_list1[13] not in ['*', '\xa0', '', '--'] else None,
                         total_phosphorus=float(data_list1[14]) if data_list1[14] not in ['*', '\xa0', '', '--'] else None,
                         total_nitrogen=float(data_list1[15]) if data_list1[15] not in ['*', '\xa0', '', '--'] else None,
                         chlorophyll_alpha=float(data_list1[16]) if data_list1[16] not in ['*', '\xa0', '', '--'] else None,
                         algal_density=float(data_list1[17]) if data_list1[17] not in ['*', '\xa0', '', '--'] else None,
                         station_status=data_list1[18])
            data1.save()
            # 使用查询条件判断数据库中是否存在相同数据
            # if Data.objects.filter(province=pd_obj, city=bd_obj, basin=bd_obj, river=rd_obj, section=sd_obj,
            #                        monitoring_time=data_list1[5], water_type=data_list1[6],water_temperature=data_list1[7],
            #                        pH=data_list1[8], dissolved_oxygen=data_list1[9], conductivity=data_list1[10],
            #                        turbidity=data_list1[11], permanganate_index=data_list1[12],ammonia_nitrogen=data_list1[13],
            #                        total_phosphorus=data_list1[14], total_nitrogen=data_list1[15], chlorophyll_alpha=data_list1[16],
            #                        algal_density=data_list1[17], station_status=data_list1[18]).exists():
            #     print("数据已存在数据库中")
            # else:
        else:
            print(f"数据不存在数据库中，未找到相关信息，无法创建数据对象")

















# city_dict.append(['110112','通州区'])
# city_dict.append(['500111','大足区'])
# city_dict.append(['500119','南川区'])
# city_dict.append(['500154','开州区'])
# city_dict.append(['500240','石柱土家族自治县'])
# city_dict.append(['513300','甘孜藏族自治州'])
# city_dict.append(['530000','上海市'])
# print(total_data)
# print(city_dict)
# print(province_dict)
# print(province_city)
# print(len(province_city))
# 用来查找不在城市列表中的城市名
# for item in total_data:
#     if item[2] not in city:
#         print(item)
# 通州区 110112 大足区 500111 南川区 500119 开州区 500154 石柱土家族自治县 500240 甘孜藏族自治州 513300
    # print(total_data)
    # print(city_id)
    # print(city)
    # print(len(city_id))
    # print(len(city))
    # print(province_id)
    # print(province)
    # print(basin)
# print(province_dict)
# print(city_dict)