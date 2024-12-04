from django.db import models


# Create your models here.
# class User(models.Model):
#     id = models.AutoField(primary_key=True,verbose_name="用户ID")
#     username = models.CharField(max_length=32, verbose_name="用户名")
#     password = models.CharField(max_length=32, verbose_name="密码")
#     email = models.CharField(max_length=32, verbose_name="邮箱")
#
#     def __str__(self):
#         return self.username
#
#     class Meta:
#         verbose_name = '用户'
#         verbose_name_plural = '用户列表'


class Province(models.Model):
    province_id = models.IntegerField(primary_key=True, verbose_name="行政代码")
    province_name = models.CharField(max_length=50, verbose_name="省份")

    def __str__(self):
        return self.province_name

    class Meta:
        verbose_name = '省份'
        verbose_name_plural = '省份数据管理'


class City(models.Model):
    city_id = models.IntegerField(primary_key=True, verbose_name="行政代码")
    province = models.ForeignKey(Province, on_delete=models.CASCADE, verbose_name="省份")
    city_name = models.CharField(max_length=50, verbose_name="城市")

    def __str__(self):
        return self.city_name

    class Meta:
        verbose_name = '城市'
        verbose_name_plural = '城市数据管理'


class Basin(models.Model):
    basin_id = models.AutoField(primary_key=True, verbose_name="流域ID")
    basin_name = models.CharField(max_length=20, verbose_name="流域")

    def __str__(self):
        return self.basin_name

    class Meta:
        verbose_name = '流域'
        verbose_name_plural = '流域数据管理'


class River(models.Model):
    river_id = models.AutoField(primary_key=True, verbose_name="河流ID")
    basin = models.ForeignKey(Basin, on_delete=models.CASCADE, verbose_name="所属流域")
    river_name = models.CharField(max_length=20, verbose_name="河流")

    def __str__(self):
        return self.river_name

    class Meta:
        verbose_name = '河流'
        verbose_name_plural = '河流数据管理'


class Section(models.Model):
    section_id = models.AutoField(primary_key=True, verbose_name="断面ID")
    province = models.ForeignKey(Province, on_delete=models.CASCADE, verbose_name="所属省份")
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="所属地区")
    basin = models.ForeignKey(Basin, on_delete=models.CASCADE, verbose_name="所属流域")
    river = models.ForeignKey(River, on_delete=models.CASCADE, verbose_name="所属河流")
    section_name = models.CharField(max_length=50, verbose_name="断面名称")

    def __str__(self):
        return self.section_name

    class Meta:
        verbose_name = '断面'
        verbose_name_plural = '断面数据管理'


class Data(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    province = models.ForeignKey(Province, on_delete=models.CASCADE, verbose_name="省份")
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="所在地区")
    basin = models.ForeignKey(Basin, on_delete=models.CASCADE, verbose_name="流域")
    river = models.ForeignKey(River, on_delete=models.CASCADE, verbose_name="所属河流")
    section = models.ForeignKey(Section, on_delete=models.CASCADE, verbose_name="断面名称")
    monitoring_time = models.DateTimeField(verbose_name="检测时间", null=True)
    water_type = models.CharField(max_length=30, verbose_name="水质类别", null=True)
    water_temperature = models.FloatField(verbose_name="水温", null=True)
    pH = models.FloatField(verbose_name="pH", null=True)
    dissolved_oxygen = models.FloatField(verbose_name="溶解氧", null=True)
    conductivity = models.FloatField(verbose_name="电导率", null=True)
    turbidity = models.FloatField(verbose_name="浊度", null=True)
    permanganate_index = models.FloatField(verbose_name="高锰酸钾指数", null=True)
    ammonia_nitrogen = models.FloatField(verbose_name="氨氮", null=True)
    total_phosphorus = models.FloatField(verbose_name="总磷", null=True)
    total_nitrogen = models.FloatField(verbose_name="总氮", null=True)
    chlorophyll_alpha = models.FloatField(verbose_name="叶绿素", null=True)
    algal_density = models.FloatField(verbose_name="藻密度", null=True)
    station_status = models.TextField(verbose_name="站点情况", null=True)

    def __str__(self):
        return self.monitoring_time.strftime('%Y-%m-%d %H:%M')

    class Meta:
        verbose_name = '数据'
        verbose_name_plural = '水质数据管理'
        unique_together = ("province", "city" , "basin", "river", "section", "monitoring_time")
        indexes = [
            models.Index(fields=['river_id']),
            models.Index(fields=['province_id']),
            models.Index(fields=['city_id']),
            models.Index(fields=['basin_id']),
            models.Index(fields=['section_id']),
            models.Index(fields=['monitoring_time']),
        ]
