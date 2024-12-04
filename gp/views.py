import io
import sys
import csv
import json
import codecs
import openpyxl
from django.db.models.functions import TruncDay
from my_package.crawler import *
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.db.models import Avg, Max, Min, Count
from datetime import datetime, timedelta
from django.http import HttpResponse, JsonResponse
from .models import Province, Data, Basin, Section, River, City
from django.core.paginator import Paginator

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='gb18030')  # 改变标准输出的默认编码
import calendar

# 目前index函数没用了
def index(request):
    # 获取当前系统时间
    current_time = datetime.now()

    # 获取当前月份的第一天和最后一天
    first_day_of_month = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    _, last_day = calendar.monthrange(current_time.year, current_time.month)
    last_day_of_month = current_time.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

    # 获取上月的第一天和最后一天
    first_day_of_last_month = first_day_of_month - timedelta(days=first_day_of_month.day)
    last_day_of_last_month = first_day_of_month - timedelta(days=1)

    # 格式化日期
    start_date_current_month = first_day_of_month.strftime('%Y-%m-%d %H:%M')
    end_date_current_month = last_day_of_month.strftime('%Y-%m-%d %H:%M')
    start_date_last_month = first_day_of_last_month.strftime('%Y-%m-%d %H:%M')
    end_date_last_month = last_day_of_last_month.strftime('%Y-%m-%d %H:%M')

    # 筛选当前月份和上月的数据
    current_month_data = Data.objects.filter(monitoring_time__range=(start_date_current_month, end_date_current_month))
    last_month_data = Data.objects.filter(monitoring_time__range=(start_date_last_month, end_date_last_month))

    # 使用 values() 和 annotate() 方法对水质类型进行分组计数
    current_month_type_counts = current_month_data.values('water_type').annotate(count=Count('id'))
    last_month_type_counts = last_month_data.values('water_type').annotate(count=Count('id'))

    # 将结果存储为字典形式，其中键为水质类型，值为对应的数量
    current_month_data_dict = {item['water_type']: item['count'] for item in current_month_type_counts}
    last_month_data_dict = {item['water_type']: item['count'] for item in last_month_type_counts}

    # 计算数据变化百分比
    change_percentage_dict = {}
    for water_type, current_count in current_month_data_dict.items():
        last_count = last_month_data_dict.get(water_type, 0)
        if last_count > 0:
            change_percentage = ((current_count - last_count) / last_count) * 100
        else:
            change_percentage = 100  # 上个月无数据时，计算增长为100%
        change_percentage_dict[water_type] = change_percentage

    # 构建需要传递给模板的数据字典
    context = {
        'current_month_data': current_month_data_dict,
        'change_percentage': change_percentage_dict,
    }

    return render(request, 'index.html', context)


def previous_crawler(request):
    if request.method == 'GET':
        return render(request, 'previous_crawler.html')


def crawler_data(request):
    if request.method == 'POST':
        page_source = crawler_source_code()
        # print("源码：\n",page_source)
        header, total_data = extract_date(page_source)
        # print("表头：\n",header)
        # print("表数据：\n",total_data)
        evaluate_water_quality(total_data)
        handle_date(total_data)
        handle_missing_data(total_data)
        # print('------------------------------------------------------------------------------------------')
        # print("数据：",total_data)
        save_to_mysql(total_data)

        # 分页逻辑
        page_number = request.GET.get('page', 1)
        paginator = Paginator(total_data, 100)  # 每页展示100条数据
        page_obj = paginator.get_page(page_number)

        return render(request, 'crawler.html', {'page_obj': page_obj})

    return render(request, 'crawler.html')


def upload(request):
    if request.method == 'POST' and request.FILES:
        for file in request.FILES.getlist('fileUpload'):
            # file_path = file.temporary_file_path()
            # print("文件路径：",file_path)
            if file.name.endswith('.html'):
                # content = file.read().decode('utf-8')
                content = file.read()
                # print("Content:\n", content)  # 输出 content 的内容
                if content is None:  # 检查 content 是否为 NoneType 对象
                    return render(request, 'upload.html')
                header, total_data = extract_date(content)
                evaluate_water_quality(total_data)
                handle_date(total_data)
                handle_missing_data(total_data)
                save_to_mysql(total_data)
                print(f"文件 {file}，已处理完成。")
            elif file.name.endswith('.csv'):
                data = []
                reader = csv.reader(codecs.iterdecode(file, 'utf-8'))
                next(reader)  # 跳过第一行（表头）
                for row in reader:
                    data.append(row)
                evaluate_water_quality(data)
                handle_date(data)
                handle_missing_data(data)
                save_to_mysql(data)
            else:
                print('不支持的文件类型')

        return render(request, 'upload.html')

    return render(request, 'upload.html')


"""
数据导出
分类：
    1.按时间范围进行导出，选定起止时间，根据起止时间在数据库中查询数据，将符合条件的数据导出为csv文件，时间格式为年月日时分秒
    2.按流域范围进行导出，导出同属于一个流域的数据，通过选择一个流域，在数据库中查询该流域，将符合条件的数据导出为csv文件
    3.按断面进行导出，导出属于同一断面的数据，通过选择一个断面，在数据库中查询该断面，将符合条件的数据导出为csv文件
    4.按河流进行导出，导出属于同一河流的数据，通过选择一个河流，在数据库中查询该河流，将符合条件的数据导出为csv文件
"""

def date_export(request):
    if request.method == 'POST':
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        start = str(start_time).replace('T', ' ')
        end = str(end_time).replace('T', ' ')

        start_datetime = datetime.strptime(start, '%Y-%m-%d %H:%M')
        end_datetime = datetime.strptime(end, '%Y-%m-%d %H:%M')

        filtered_data = Data.objects.filter(monitoring_time__range=(start_datetime, end_datetime))[:50]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="data_by_time_range.csv"'

        writer = csv.writer(response)
        writer.writerow(
            ['省份', '城市', '流域', '河流', '断面名称', '检测时间', '水质类别', '水温', 'pH', '溶解氧', '电导率',
             '浊度', '高锰酸钾指数', '氨氮', '总磷', '总氮', '叶绿素', '藻密度', '站点情况'])
        for data in filtered_data:
            writer.writerow([data.province.province_name, data.city.city_name, data.basin.basin_name,
                             data.river.river_name, data.section.section_name,
                             data.monitoring_time.strftime('%Y-%m-%d %H:%M'),
                             data.water_type, data.water_temperature, data.pH, data.dissolved_oxygen,
                             data.conductivity, data.turbidity, data.permanganate_index, data.ammonia_nitrogen,
                             data.total_phosphorus, data.total_nitrogen, data.chlorophyll_alpha, data.algal_density,
                             data.station_status])

        return response
    else:
        return render(request, 'date_export.html')


def basin_export(request):
    basins = Basin.objects.all()
    for basin in basins:
        d1, d2 = basin.basin_id, basin.basin_name
        print(d1, d2)

    if request.method == 'POST':
        basin_id = request.POST.get('basin_id')
        filtered_data = Data.objects.filter(basin_id=basin_id)[:50]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="data_by_basin.csv"'

        writer = csv.writer(response)
        writer.writerow(
            ['省份', '城市', '流域', '河流', '断面名称', '检测时间', '水质类别', '水温', 'pH', '溶解氧', '电导率',
             '浊度', '高锰酸钾指数', '氨氮', '总磷', '总氮', '叶绿素', '藻密度', '站点情况'])
        for data in filtered_data:
            writer.writerow([data.province.province_name, data.city.city_name, data.basin.basin_name,
                             data.river.river_name, data.section.section_name,
                             data.monitoring_time.strftime('%Y-%m-%d %H:%M:%S'),
                             data.water_type, data.water_temperature, data.pH, data.dissolved_oxygen,
                             data.conductivity, data.turbidity, data.permanganate_index, data.ammonia_nitrogen,
                             data.total_phosphorus, data.total_nitrogen, data.chlorophyll_alpha, data.algal_density,
                             data.station_status])

        return response
    else:
        return render(request, 'basin_export.html', {'basins': basins})


def section_export(request):
    sections = Section.objects.all()

    if request.method == 'POST':
        section_id = request.POST.get('section_id')
        filtered_data = Data.objects.filter(section_id=section_id)[:50]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="data_by_section.csv"'

        writer = csv.writer(response)
        writer.writerow(
            ['省份', '城市', '流域', '河流', '断面名称', '检测时间', '水质类别', '水温', 'pH', '溶解氧', '电导率',
             '浊度', '高锰酸钾指数', '氨氮', '总磷', '总氮', '叶绿素', '藻密度', '站点情况'])
        for data in filtered_data:
            writer.writerow([data.province.province_name, data.city.city_name, data.basin.basin_name,
                             data.river.river_name, data.section.section_name,
                             data.monitoring_time.strftime('%Y-%m-%d %H:%M:%S'),
                             data.water_type, data.water_temperature, data.pH, data.dissolved_oxygen,
                             data.conductivity, data.turbidity, data.permanganate_index, data.ammonia_nitrogen,
                             data.total_phosphorus, data.total_nitrogen, data.chlorophyll_alpha, data.algal_density,
                             data.station_status])

        return response
    else:
        return render(request, 'section_export.html', {'sections': sections})


def river_export(request):
    rivers = River.objects.all()

    if request.method == 'POST':
        river_id = request.POST.get('river_id')
        filtered_data = Data.objects.filter(river_id=river_id)[:50]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="data_by_river.csv"'

        writer = csv.writer(response)
        writer.writerow(
            ['省份', '城市', '流域', '河流', '断面名称', '检测时间', '水质类别', '水温', 'pH', '溶解氧', '电导率',
             '浊度', '高锰酸钾指数', '氨氮', '总磷', '总氮', '叶绿素', '藻密度', '站点情况'])
        for data in filtered_data:
            writer.writerow([data.province.province_name, data.city.city_name, data.basin.basin_name,
                             data.river.river_name, data.section.section_name,
                             data.monitoring_time.strftime('%Y-%m-%d %H:%M:%S'),
                             data.water_type, data.water_temperature, data.pH, data.dissolved_oxygen,
                             data.conductivity, data.turbidity, data.permanganate_index, data.ammonia_nitrogen,
                             data.total_phosphorus, data.total_nitrogen, data.chlorophyll_alpha, data.algal_density,
                             data.station_status])

        return response
    else:
        return render(request, 'river_export.html', {'rivers': rivers})


"""
数据统计
分类：
    1.按照地域划分进行数据统计，按省份、城市、流域、河流、断面统计数据，计算一段时间范围内各省份、城市、流域、河流、断面的水质各项数据的平均值、最大值、最小值以表格的形式展示在前端页面
    2.按省份和城市统计各个省份、城市的水质占比情况，统计所有数据中各个类型水质按省份和城市分别划分的占比，以饼图的形式展示在前端页面
    3.按流域、河流统计随时间趋势，水质各项数据的均值变化趋势，统计一段时间范围内的变化趋势，以折线图的形式展示在前端页面
分类：
    1.按时间范围进行导出，选定起止时间，根据起止时间在数据库中查询数据，将符合条件的数据导出为csv文件，时间格式为年月日时分秒
    2.按流域范围进行导出，导出同属于一个流域的数据，通过选择一个流域，在数据库中查询该流域，将符合条件的数据导出为csv文件
    3.按断面进行导出，导出属于同一断面的数据，通过选择一个断面，在数据库中查询该断面，将符合条件的数据导出为csv文件
    4.按河流进行导出，导出属于同一河流的数据，通过选择一个河流，在数据库中查询该河流，将符合条件的数据导出为csv文件

按省份或城市聚合数据：
计算每个省份或城市水质参数（如 pH、溶解氧）的平均值或最大值。
统计每个省份或城市在特定时间段内的监测次数。
按河流或流域筛选数据：
总结特定河流或流域的水质数据。
分析选定河流或流域的时间趋势。
时间分析：
分析所有断面水质参数的时间趋势。
计算水质指标的季节平均值或变化。
水质分类：
基于阈值（如 pH、溶解氧水平）对水质进行分类，并报告落入不同质量类别的比例
1. **按地理位置划分：**
   - 按省份、城市、流域、河流等地理区域划分数据，可以帮助了解不同地区水质情况的地理分布情况。

2. **按时间划分：**
   - 按年度、季度、月份等时间维度划分数据，可以分析水质随时间的变化趋势，发现季节性变化或长期趋势。

3. **按水质指标划分：**
   - 按不同的水质指标（如 pH 值、溶解氧、氨氮、总磷等）对数据进行划分，可以了解不同水质指标的水质状况。

4. **按监测点类型划分：**
   - 按照监测点的类型（如表层水、地下水、河流、湖泊、水库等）划分数据，可以分析不同类型水体的水质情况。

5. **按水质等级划分：**
   - 将水质数据按照水质等级（如优质水、良好水、一般水、劣质水）进行划分，可以快速了解水质分布和占比情况。

6. **综合划分：**
   - 综合考虑地理位置、时间、水质指标等多个因素进行划分，可以得到更全面的水质数据统计结果。

"""


def statistic(request):
    provinces = Province.objects.all()

    if request.method == 'POST':
        # 获取表单提交的省份和时间范围
        province_id = request.POST.get('province_id')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        start = str(start_date_str).replace('T', ' ')
        end = str(end_date_str).replace('T', ' ')

        # 将日期字符串转换为 datetime 对象
        start_date = datetime.strptime(start, '%Y-%m-%d %H:%M')
        end_date = datetime.strptime(end, '%Y-%m-%d %H:%M')

        # 查询指定省份和时间范围内的水质数据，并排除值为-1的数据
        province = Province.objects.get(province_id=province_id)
        data_queryset = Data.objects.filter(
            province=province,
            monitoring_time__range=(start_date, end_date),
            pH__gt=-1,
            dissolved_oxygen__gt=-1,
            conductivity__gt=-1,
            turbidity__gt=-1,
            permanganate_index__gt=-1,
            ammonia_nitrogen__gt=-1,
            total_phosphorus__gt=-1,
            total_nitrogen__gt=-1
        )

        # 计算水质数据的平均值、最大值和最小值并保留两位小数
        water_quality_stats = data_queryset.aggregate(
            avg_pH=Avg('pH'),
            max_pH=Max('pH'),
            min_pH=Min('pH'),
            avg_dissolved_oxygen=Avg('dissolved_oxygen'),
            max_dissolved_oxygen=Max('dissolved_oxygen'),
            min_dissolved_oxygen=Min('dissolved_oxygen'),
            avg_conductivity=Avg('conductivity'),
            max_conductivity=Max('conductivity'),
            min_conductivity=Min('conductivity'),
            avg_turbidity=Avg('turbidity'),
            max_turbidity=Max('turbidity'),
            min_turbidity=Min('turbidity'),
            avg_permanganate_index=Avg('permanganate_index'),
            max_permanganate_index=Max('permanganate_index'),
            min_permanganate_index=Min('permanganate_index'),
            avg_ammonia_nitrogen=Avg('ammonia_nitrogen'),
            max_ammonia_nitrogen=Max('ammonia_nitrogen'),
            min_ammonia_nitrogen=Min('ammonia_nitrogen'),
            avg_total_phosphorus=Avg('total_phosphorus'),
            max_total_phosphorus=Max('total_phosphorus'),
            min_total_phosphorus=Min('total_phosphorus'),
            avg_total_nitrogen=Avg('total_nitrogen'),
            max_total_nitrogen=Max('total_nitrogen'),
            min_total_nitrogen=Min('total_nitrogen')
        )

        # 将聚合结果格式化为两位小数
        formatted_stats = {key: round(value, 2) if isinstance(value, float) else value
                           for key, value in water_quality_stats.items()}

        # 构建数据上下文，用于传递到模板中
        context = {
            'provinces': provinces,
            'province_name': province.province_name,
            'start_date': start_date,
            'end_date': end_date,
            'water_quality_stats': formatted_stats
        }

        return render(request, 'territory_statistic.html', context)

    else:
        # 如果是 GET 请求，返回表单页面
        return render(request, 'territory_statistic.html', {'provinces': provinces})


"""
数据统计
    2.按省份和城市统计各个省份、城市的水质占比情况，统计所有数据中各个类型水质按省份和城市分别划分的占比，
    以饼图的形式展示在前端页面
"""


@csrf_exempt
def get_cities_by_province(request):
    if request.method == 'POST':
        data = json.loads(request.body)  # 解析前端传递的POST数据体
        province_id = data.get('province_id')  # 获取前端传递的省份ID

        # 根据省份ID查询数据库，获取该省份的城市列表
        cities = City.objects.filter(province_id=province_id).values('city_id', 'city_name')
        city_list = list(cities)
        return JsonResponse({'cities': city_list})
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


def city_statistic(request):
    provinces = Province.objects.all()

    if request.method == 'POST':
        province_id = request.POST.get('province_id')
        city_id = request.POST.get('city_id')
        province_name = Province.objects.get(province_id=province_id).province_name
        city_name = City.objects.get(city_id=city_id).city_name

        data_set = Data.objects.filter(city_id=city_id)
        total_count = data_set.count()

        water_type_counts = data_set.values('water_type').annotate(count=Count('water_type'))
        labels = [item['water_type'] for item in water_type_counts]
        counts = [item['count'] for item in water_type_counts]
        # 计算百分比
        percentages = [count / total_count * 100 if total_count > 0 else 0 for count in counts]
        percentages = [f"{percentage:.2f}" for percentage in percentages]

        combined_list = list(zip(labels, counts, percentages))

        # print(labels)
        # print(counts)

        context = {
            'provinces': provinces,
            'labels': labels,
            'counts': counts,
            'selected_province': province_name,
            'selected_city': city_name,
            'combined_list': combined_list
        }

        return render(request, 'city_statistic.html', context)

    return render(request, 'city_statistic.html', {'provinces': provinces})


def section_statistic(request):
    sections = Section.objects.all()

    if request.method == 'POST':
        # 获取表单提交的省份和时间范围
        section_id = request.POST.get('section_id')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        start = str(start_date_str).replace('T', ' ')
        end = str(end_date_str).replace('T', ' ')

        # 将日期字符串转换为 datetime 对象
        start_date = datetime.strptime(start, '%Y-%m-%d %H:%M')
        end_date = datetime.strptime(end, '%Y-%m-%d %H:%M')

        # 按天分组并计算均值
        daily_avg_data = Data.objects.filter(
            section__section_id=section_id,
            monitoring_time__range=(start_date, end_date),
            pH__gt=-1,
            dissolved_oxygen__gt=-1,
            conductivity__gt=-1,
            turbidity__gt=-1,
            permanganate_index__gt=-1,
            ammonia_nitrogen__gt=-1,
            total_phosphorus__gt=-1,
            total_nitrogen__gt=-1
        ).annotate(
            day=TruncDay('monitoring_time')
        ).values('day').annotate(
            avg_pH=Avg('pH'),
            avg_dissolved_oxygen=Avg('dissolved_oxygen'),
            avg_conductivity=Avg('conductivity'),
            avg_turbidity=Avg('turbidity'),
            avg_permanganate_index=Avg('permanganate_index'),
            avg_ammonia_nitrogen=Avg('ammonia_nitrogen'),
            avg_total_phosphorus=Avg('total_phosphorus'),
            avg_total_nitrogen=Avg('total_nitrogen')
        ).order_by('day')

        # 准备图表数据
        labels = [entry['day'].strftime('%Y-%m-%d') for entry in daily_avg_data]

        chart_data = {
            'pH': [entry['avg_pH'] for entry in daily_avg_data],
            'dissolved_oxygen': [entry['avg_dissolved_oxygen'] for entry in daily_avg_data],
            'conductivity': [entry['avg_conductivity'] for entry in daily_avg_data],
            'turbidity': [entry['avg_turbidity'] for entry in daily_avg_data],
            'permanganate_index': [entry['avg_permanganate_index'] for entry in daily_avg_data],
            'ammonia_nitrogen': [entry['avg_ammonia_nitrogen'] for entry in daily_avg_data],
            'total_phosphorus': [entry['avg_total_phosphorus'] for entry in daily_avg_data],
            'total_nitrogen': [entry['avg_total_nitrogen'] for entry in daily_avg_data],
        }

        # 查询指定省份和时间范围内的水质数据，并排除值为-1的数据
        section = Section.objects.get(section_id=section_id)
        data_queryset_1 = Data.objects.filter(
            section=section,
            monitoring_time__range=(start_date, end_date),
            pH__gt=-1,
            dissolved_oxygen__gt=-1,
            conductivity__gt=-1,
            turbidity__gt=-1,
            permanganate_index__gt=-1,
            ammonia_nitrogen__gt=-1,
            total_phosphorus__gt=-1,
            total_nitrogen__gt=-1
        ).order_by('monitoring_time')  # 按照监测时间排序

        # 计算水质数据的平均值、最大值和最小值并保留两位小数
        water_quality_stats = data_queryset_1.aggregate(
            avg_pH=Avg('pH'),
            max_pH=Max('pH'),
            min_pH=Min('pH'),
            avg_dissolved_oxygen=Avg('dissolved_oxygen'),
            max_dissolved_oxygen=Max('dissolved_oxygen'),
            min_dissolved_oxygen=Min('dissolved_oxygen'),
            avg_conductivity=Avg('conductivity'),
            max_conductivity=Max('conductivity'),
            min_conductivity=Min('conductivity'),
            avg_turbidity=Avg('turbidity'),
            max_turbidity=Max('turbidity'),
            min_turbidity=Min('turbidity'),
            avg_permanganate_index=Avg('permanganate_index'),
            max_permanganate_index=Max('permanganate_index'),
            min_permanganate_index=Min('permanganate_index'),
            avg_ammonia_nitrogen=Avg('ammonia_nitrogen'),
            max_ammonia_nitrogen=Max('ammonia_nitrogen'),
            min_ammonia_nitrogen=Min('ammonia_nitrogen'),
            avg_total_phosphorus=Avg('total_phosphorus'),
            max_total_phosphorus=Max('total_phosphorus'),
            min_total_phosphorus=Min('total_phosphorus'),
            avg_total_nitrogen=Avg('total_nitrogen'),
            max_total_nitrogen=Max('total_nitrogen'),
            min_total_nitrogen=Min('total_nitrogen')
        )

        # 将聚合结果格式化为两位小数
        formatted_stats = {key: round(value, 2) if isinstance(value, float) else value
                           for key, value in water_quality_stats.items()}

        # 构建数据上下文，用于传递到模板中
        context = {
            'sections': sections,
            'section_name': section.section_name,
            'start_date': start_date,
            'end_date': end_date,
            'chart_labels': labels,
            'chart_data': chart_data,
            'water_quality_stats': formatted_stats
        }

        return render(request, 'section_statistic.html', context)

    else:
        # 如果是 GET 请求，返回表单页面
        return render(request, 'section_statistic.html', {'sections': sections})


"""
后台管理首页
1.全国水质类型占比
2.最新日期的水质指标数据统计（水质指标的最大值、最小值）
3.数据库中存在的数据最近一个月内的水质指标变化曲线图
"""
from datetime import timedelta

def home_page(request):
    if request.method == 'GET':
        # 全国水质类型占比
        # 获取所有水质类别及其数量
        water_quality_counts = Data.objects.values('water_type').annotate(count=Count('water_type'))
        labels = [item['water_type'] for item in water_quality_counts]
        counts = [item['count'] for item in water_quality_counts]

        # print("类型：", type(water_quality_counts))
        # print("水质类别及数量数据：", water_quality_counts)
        # 计算总数
        total_count = Data.objects.count()
        percentages = [count / total_count * 100 if total_count > 0 else 0 for count in counts]
        percentages = [f"{percentage:.2f}" for percentage in percentages]

        combined_list = list(zip(labels, counts, percentages))
        # 计算占比，并生成结果列表
        # statistics = []
        # for item in water_quality_counts:
        #     percentage = (item['count'] / total_count) * 100
        #     statistics.append({
        #         'water_type': item['water_type'],
        #         'count': item['count'],
        #         'percentage': round(percentage, 2)  # 四舍五入保留两位小数
        #     })
        # print("水质占比：", statistics)

        # 获取最新日期的水质指标数据统计（水质指标的最大值、最小值）
        latest_data = Data.objects.order_by('-monitoring_time').first()
        # print("最近一条数据：", latest_data)
        latest_date = latest_data.monitoring_time
        # print("最近日期：", latest_date)
        start_date = latest_date - timedelta(days=30)
        # print("最近一个月的开始日期", start_date, )
        end_date = latest_date
        # print("最近日期：", end_date)

        # 将日期字符串转换为 datetime 对象
        s_date = start_date.strftime('%Y-%m-%d %H:%M')
        e_date = end_date.strftime('%Y-%m-%d %H:%M')

        # 按天分组并计算均值
        daily_avg_data = Data.objects.filter(
            city__city_id=410100,
            monitoring_time__range=(s_date, e_date),
            pH__gt=-1,
            dissolved_oxygen__gt=-1,
            conductivity__gt=-1,
            turbidity__gt=-1,
            permanganate_index__gt=-1,
            ammonia_nitrogen__gt=-1,
            total_phosphorus__gt=-1,
            total_nitrogen__gt=-1
        ).annotate(
            day=TruncDay('monitoring_time')
        ).values('day').annotate(
            avg_pH=Avg('pH'),
            avg_dissolved_oxygen=Avg('dissolved_oxygen'),
            avg_conductivity=Avg('conductivity'),
            avg_turbidity=Avg('turbidity'),
            avg_permanganate_index=Avg('permanganate_index'),
            avg_ammonia_nitrogen=Avg('ammonia_nitrogen'),
            avg_total_phosphorus=Avg('total_phosphorus'),
            avg_total_nitrogen=Avg('total_nitrogen')
        ).order_by('day')

        # 准备图表数据
        labelss = [entry['day'].strftime('%Y-%m-%d') for entry in daily_avg_data]

        chart_data = {
            'pH': [entry['avg_pH'] for entry in daily_avg_data],
            'dissolved_oxygen': [entry['avg_dissolved_oxygen'] for entry in daily_avg_data],
            'conductivity': [entry['avg_conductivity'] for entry in daily_avg_data],
            'turbidity': [entry['avg_turbidity'] for entry in daily_avg_data],
            'permanganate_index': [entry['avg_permanganate_index'] for entry in daily_avg_data],
            'ammonia_nitrogen': [entry['avg_ammonia_nitrogen'] for entry in daily_avg_data],
            'total_phosphorus': [entry['avg_total_phosphorus'] for entry in daily_avg_data],
            'total_nitrogen': [entry['avg_total_nitrogen'] for entry in daily_avg_data],
        }

        latest_stats = {
            'max_pH': Data.objects.filter(monitoring_time=latest_date).exclude(pH=-1).aggregate(max_pH=Max('pH'))['max_pH'],
            'min_pH': Data.objects.filter(monitoring_time=latest_date).exclude(pH=-1).aggregate(min_pH=Min('pH'))['min_pH'],
            'max_dissolved_oxygen': Data.objects.filter(monitoring_time=latest_date).exclude(dissolved_oxygen=-1).aggregate(max_dissolved_oxygen=Max('dissolved_oxygen'))['max_dissolved_oxygen'],
            'min_dissolved_oxygen': Data.objects.filter(monitoring_time=latest_date).exclude(dissolved_oxygen=-1).aggregate(min_dissolved_oxygen=Min('dissolved_oxygen'))['min_dissolved_oxygen'],
            'max_conductivity': Data.objects.filter(monitoring_time=latest_date).exclude(conductivity=-1).aggregate(max_conductivity=Max('conductivity'))['max_conductivity'],
            'min_conductivity': Data.objects.filter(monitoring_time=latest_date).exclude(conductivity=-1).aggregate(min_conductivity=Min('conductivity'))['min_conductivity'],
            'max_turbidity': Data.objects.filter(monitoring_time=latest_date).exclude(turbidity=-1).aggregate( max_turbidity=Max('turbidity'))['max_turbidity'],
            'min_turbidity': Data.objects.filter(monitoring_time=latest_date).exclude(turbidity=-1).aggregate(min_turbidity=Min('turbidity'))['min_turbidity'],
            'max_permanganate_index':Data.objects.filter(monitoring_time=latest_date).exclude(permanganate_index=-1).aggregate( max_permanganate_index=Max('permanganate_index'))['max_permanganate_index'],
            'min_permanganate_index': Data.objects.filter(monitoring_time=latest_date).exclude(permanganate_index=-1).aggregate(min_permanganate_index=Min('permanganate_index'))['min_permanganate_index'],
            'max_ammonia_nitrogen':Data.objects.filter(monitoring_time=latest_date).exclude(ammonia_nitrogen=-1).aggregate(max_ammonia_nitrogen=Max('ammonia_nitrogen'))['max_ammonia_nitrogen'],
            'min_ammonia_nitrogen':Data.objects.filter(monitoring_time=latest_date).exclude(ammonia_nitrogen=-1).aggregate(min_ammonia_nitrogen=Min('ammonia_nitrogen'))['min_ammonia_nitrogen'],
            'max_total_phosphorus':Data.objects.filter(monitoring_time=latest_date).exclude(total_phosphorus=-1).aggregate(max_total_phosphorus=Max('total_phosphorus'))['max_total_phosphorus'],
            'min_total_phosphorus':Data.objects.filter(monitoring_time=latest_date).exclude(total_phosphorus=-1).aggregate(min_total_phosphorus=Min('total_phosphorus'))['min_total_phosphorus'],
            'max_total_nitrogen': Data.objects.filter(monitoring_time=latest_date).exclude(total_nitrogen=-1).aggregate(max_total_nitrogen=Max('total_nitrogen'))['max_total_nitrogen'],
            'min_total_nitrogen': Data.objects.filter(monitoring_time=latest_date).exclude(total_nitrogen=-1).aggregate( min_total_nitrogen=Min('total_nitrogen'))['min_total_nitrogen'],
        }

        context = {
            'latest_date': latest_date,
            'start_date': start_date,
            'end_date': end_date,
            'latest_stats': latest_stats,
            'labels': labels,
            'counts': counts,
            'combined_list': combined_list,
            'chart_labels': labelss,
            'chart_data': chart_data,
        }
        # print("最新日期的水质指标数据: ", context)

    return render(request, 'home_page.html', context)
