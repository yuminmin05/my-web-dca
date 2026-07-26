from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal

class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    is_set50 = models.BooleanField(default=True)
    
    # ฟิลด์ที่เพิ่มใหม่ให้เหมือน SETTRADE
    last_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="ราคาล่าสุด")
    change = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="เปลี่ยนแปลง")
    percent_change = models.FloatField(default=0.0, verbose_name="% เปลี่ยนแปลง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="อัปเดตล่าสุด")

    def __str__(self):
        return self.symbol

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, verbose_name="เกี่ยวกับตัวเอง")
    phone = models.CharField(max_length=20, blank=True, verbose_name="เบอร์โทรศัพท์")
    preferred_language = models.CharField(max_length=10, default='th', choices=[('th', 'ไทย'), ('en', 'English')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profile of {self.user.username}"

class UserPlan(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    monthly_investment = models.DecimalField(max_digits=10, decimal_places=2, default=5000.00, validators=[MinValueValidator(Decimal('0.01'))])
    
    duration_years = models.IntegerField(default=10, validators=[MinValueValidator(1)]) # ระยะเวลาการลงทุน (ปี)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, default=1000000.00, validators=[MinValueValidator(Decimal('0.01'))]) # เป้าหมายทางการเงิน
    
    selected_stocks = models.TextField(default="ADVANC,AOT,CPALL,KBANK,PTT")
    
    # GA Results
    last_optimized_weights = models.JSONField(null=True, blank=True, verbose_name="ผลลัพธ์ GA ล่าสุด")
    last_expected_return = models.FloatField(null=True, blank=True, verbose_name="ผลตอบแทนคาดหวัง")
    last_sharpe_ratio = models.FloatField(null=True, blank=True, verbose_name="Sharpe Ratio")
    last_chart_labels = models.JSONField(null=True, blank=True, verbose_name="ป้ายกราฟผลลัพธ์ล่าสุด")
    last_chart_data = models.JSONField(null=True, blank=True, verbose_name="ข้อมูลกราฟผลลัพธ์ล่าสุด")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Plan of {self.user.username}"

class DCAPreset(models.Model):
    """แผนการลงทุน DCA สำเร็จรูป"""
    name = models.CharField(max_length=100, verbose_name="ชื่อแผน")
    description = models.TextField(verbose_name="คำอธิบาย")
    monthly_investment = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="เงินลงทุนรายเดือน")
    duration_years = models.IntegerField(verbose_name="ระยะเวลา (ปี)")
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="เป้าหมายทางการเงิน")
    selected_stocks = models.TextField(verbose_name="หุ้นที่เลือก")
    expected_return = models.FloatField(verbose_name="ผลตอบแทนคาดหวัง (%)")
    risk_level = models.CharField(max_length=20, choices=[('low', 'ต่ำ'), ('medium', 'ปานกลาง'), ('high', 'สูง')], verbose_name="ระดับความเสี่ยง")
    is_active = models.BooleanField(default=True, verbose_name="ใช้งานอยู่")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "แผน DCA สำเร็จรูป"
        verbose_name_plural = "แผน DCA สำเร็จรูป"
    
    def __str__(self):
        return self.name

class UserInvestmentRecord(models.Model):
    """บันทึกการลงทุนของผู้ใช้"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investment_records')
    month = models.DateField(verbose_name="เดือนการลงทุน")
    amount_invested = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="จำนวนเงินที่ลงทุน")
    notes = models.TextField(blank=True, verbose_name="หมายเหตุ")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'month')
        ordering = ['-month']
        verbose_name = "บันทึกการลงทุน"
        verbose_name_plural = "บันทึกการลงทุน"
    
    def __str__(self):
        return f"{self.user.username} - {self.month}"


class GAResultSnapshot(models.Model):
    """เก็บ snapshot ผลการรัน GA แต่ละครั้ง (history)
    เก็บไว้เพื่อให้ผู้ใช้สามารถย้อนดูหรือดาวน์โหลดผลย้อนหลังได้
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ga_snapshots')
    saved_at = models.DateTimeField(auto_now_add=True)
    expected_return = models.FloatField(null=True, blank=True)
    sharpe_ratio = models.FloatField(null=True, blank=True)
    weights = models.JSONField(null=True, blank=True)
    chart_labels = models.JSONField(null=True, blank=True)
    chart_data = models.JSONField(null=True, blank=True)
    final_portfolio_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    monthly_investment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    duration_years = models.IntegerField(null=True, blank=True)
    target_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "GA Result Snapshot"
        verbose_name_plural = "GA Result Snapshots"
        ordering = ['-saved_at']

    def __str__(self):
        return f"GA Snapshot {self.user.username} @ {self.saved_at.strftime('%Y-%m-%d %H:%M')}"