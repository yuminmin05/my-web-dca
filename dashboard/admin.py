from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import yfinance as yf
import logging
import concurrent.futures
from .models import Stock, UserPlan, UserProfile, DCAPreset, UserInvestmentRecord, GAResultSnapshot

logger = logging.getLogger(__name__)

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'display_last_price', 'display_change', 'display_percent_change', 'is_set50', 'updated_at')
    list_display_links = ('symbol',)
    search_fields = ('symbol',)
    list_filter = ('is_set50',)
    ordering = ('-is_set50', 'symbol')
    list_per_page = 30
    actions = ['update_stock_prices', 'seed_missing_stock_records']
    actions_on_top = True
    save_on_top = True
    show_full_result_count = True

    # 2. ย้ายฟังก์ชันอัปเดตราคามาไว้ใน Class นี้เลย
    @admin.action(description='อัปเดตราคาหุ้นจาก Yahoo Finance')
    def update_stock_prices(self, request, queryset):
        for stock in queryset:
            self._fetch_update(stock)

    @admin.action(description='สร้างข้อมูลหุ้นที่ขาดหาย')
    def seed_missing_stock_records(self, request, queryset):
        default_symbols = ['ADVANC', 'AOT', 'BBL', 'CPALL', 'KBANK', 'PTT', 'SCB', 'SET', 'TRUE', 'BBL']
        for symbol in default_symbols:
            Stock.objects.get_or_create(symbol=symbol, defaults={'is_set50': True})
        messages.success(request, 'สร้างข้อมูลหุ้นเริ่มต้นเรียบร้อยแล้ว')

    # 3. จัดกลุ่มหน้า Detail View ใหม่
    fieldsets = (
        ('กระดานสรุปราคา (SETTRADE Style)', {
            'fields': ('settrade_style_dashboard',),
        }),
        ('ลิงก์ข้อมูลเพิ่มเติม', {
            'fields': ('view_on_settrade',),
        }),
        ('ข้อมูลพื้นฐานในระบบ (Raw Data)', {
            'fields': ('symbol', 'is_set50', 'last_price', 'change', 'percent_change', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('settrade_style_dashboard', 'updated_at', 'view_on_settrade', 'last_price', 'change', 'percent_change')

    class Media:
        css = {
            'all': ('dashboard/css/admin_custom.css',)
        }

    # ==========================================
    # 4. ฟังก์ชันสร้างการ์ดเหมือน SETTRADE
    # ==========================================
    def _to_decimal(self, value, default=0.0):
        try:
            if value is None:
                return default
            if isinstance(value, str):
                return float(value.replace(',', ''))
            return float(value)
        except (ValueError, TypeError):
            return default

    def _format_number(self, value, precision=2):
        amount = self._to_decimal(value)
        return f"{amount:,.{precision}f}"

    def settrade_style_dashboard(self, obj):
        if obj.last_price is None or self._to_decimal(obj.last_price) == 0:
            return format_html(
                '<div class="stock-live-card stock-live-card--empty">'
                '<div class="stock-live-card__title">{}</div>'
                '<div class="stock-live-card__note">{}</div>'
                '</div>',
                'Stock Live Quote',
                'ไม่มีข้อมูลราคาเรียลไทม์ ให้เลือก Action หรือกดแก้ไขเพื่อโหลดข้อมูลล่าสุด'
            )

        change_value = self._to_decimal(obj.change)
        if change_value > 0:
            card_type = 'stock-live-card--positive'
            icon = '▲'
            sign = '+'
        elif change_value < 0:
            card_type = 'stock-live-card--negative'
            icon = '▼'
            sign = ''
        else:
            card_type = 'stock-live-card--neutral'
            icon = '-'
            sign = ''

        formatted_last_price = self._format_number(obj.last_price)
        formatted_change = self._format_number(change_value)
        formatted_percent = self._format_number(obj.percent_change)

        html = """
        <div class="stock-live-card {}">
            <div class="stock-live-card__header">
                <div class="stock-live-card__symbol">{}</div>
                <div class="stock-live-card__label">Real-time Quote</div>
            </div>
            <div class="stock-live-card__body">
                <div class="stock-live-card__price">{}</div>
                <div class="stock-live-card__movement">{} {}</div>
            </div>
            <div class="stock-live-card__footer">{}{}</div>
        </div>
        """
        return format_html(html, card_type, obj.symbol, formatted_last_price, icon, formatted_change, sign, formatted_percent)
    settrade_style_dashboard.short_description = ""

    def view_on_settrade(self, obj):
        url = f"https://www.settrade.com/th/equities/quote/{obj.symbol}/main"
        return format_html('<a href="{}" target="_blank" class="button button-view-settrade">ดูข้อมูลเชิงลึกบน SETTRADE.COM ↗️</a>', url)
    view_on_settrade.short_description = "เว็บไซต์ภายนอก"

    def display_change(self, obj):
        change_value = self._to_decimal(obj.change)
        color = "green" if change_value > 0 else "red" if change_value < 0 else "black"
        symbol = "+" if change_value > 0 else ""
        formatted_change = self._format_number(change_value)
        return format_html('<span style="color: {}; font-weight: bold;">{}{}</span>', color, symbol, formatted_change)
    display_change.short_description = "เปลี่ยนแปลง"

    def display_percent_change(self, obj):
        percent_value = self._to_decimal(obj.percent_change)
        color = "green" if percent_value > 0 else "red" if percent_value < 0 else "black"
        symbol = "+" if percent_value > 0 else ""
        formatted_pct = self._format_number(percent_value)
        return format_html('<span style="color: {}; font-weight: bold;">{}{}%</span>', color, symbol, formatted_pct)
    display_percent_change.short_description = "% เปลี่ยนแปลง"

    def display_last_price(self, obj):
        formatted_price = self._format_number(obj.last_price)
        return format_html('<span style="font-weight: bold;">{}</span>', formatted_price)
    display_last_price.short_description = "ราคาล่าสุด"

    # ==========================================
    # 5. ฟังก์ชันอัปเดตอัตโนมัติเมื่อกดเข้ามาดูรายละเอียด
    # ==========================================
    def get_object(self, request, object_id, from_field=None):
        # ดึงออบเจกต์ของหุ้นตัวที่เรากำลังคลิกเข้ามา
        obj = super().get_object(request, object_id, from_field)
        
        # ถ้าเจอข้อมูล ให้แอบไปดึงราคาล่าสุดแบบ Real-time ทันที
        if obj:
            self._fetch_update(obj)

        # คืนค่าข้อมูลที่สดใหม่ที่สุดไปสร้างหน้าเว็บ
        return obj

    def _fetch_update(self, stock):
        """Helper: fetch latest price for a stock and save it. Returns True on success."""
        ticker = f"{stock.symbol}.BK"
        try:
            data = yf.Ticker(ticker)
            hist = data.history(period="2d", timeout=10)
            if len(hist) >= 2:
                prev_close = hist['Close'].iloc[0]
                last_price = hist['Close'].iloc[1]
                change = last_price - prev_close
                pct_change = (change / prev_close) * 100

                stock.last_price = float(round(float(last_price), 2))
                stock.change = float(round(float(change), 2))
                stock.percent_change = float(round(float(pct_change), 2))
                stock.save(update_fields=['last_price', 'change', 'percent_change', 'updated_at'])
                return True
        except Exception:
            logger.exception("Failed to fetch/update stock %s", stock.symbol)
        return False

    def changelist_view(self, request, extra_context=None):
        """Override changelist to perform live updates for SET50 stocks when opening the list."""
        response = super().changelist_view(request, extra_context)
        try:
            qs = self.get_queryset(request).filter(is_set50=True)
            stocks = list(qs)
            if stocks:
                # Fetch updates concurrently but bound total wait time
                updated = 0
                with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
                    futures = {ex.submit(self._fetch_update, s): s for s in stocks}
                    done, not_done = concurrent.futures.wait(futures.keys(), timeout=15)
                    for fut in done:
                        try:
                            if fut.result():
                                updated += 1
                        except Exception:
                            pass
                messages.info(request, f"อัปเดตราคาสำหรับ SET50: {updated}/{len(stocks)} รายการ (เรียลไทม์)")
        except Exception:
            logger.exception("Live update for SET50 failed")
        return response

@admin.register(UserPlan)
class UserPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'monthly_investment', 'duration_years', 'target_amount', 'last_optimized_at')
    search_fields = ('user__username',) 
    list_filter = ('duration_years',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('ข้อมูลผู้ใช้', {
            'fields': ('user',),
        }),
        ('พารามิเตอร์การลงทุน', {
            'fields': ('monthly_investment', 'duration_years', 'target_amount', 'selected_stocks'),
        }),
        ('ผลลัพธ์ GA ล่าสุด', {
            'fields': ('last_expected_return', 'last_sharpe_ratio', 'last_optimized_weights'),
        }),
        ('วันที่', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def last_optimized_at(self, obj):
        return obj.updated_at.strftime('%d/%m/%Y %H:%M') if obj.updated_at else 'ยังไม่ได้'
    last_optimized_at.short_description = 'อัปเดตล่าสุด'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'preferred_language', 'created_at')
    search_fields = ('user__username', 'user__email')
    list_filter = ('preferred_language',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(DCAPreset)
class DCAPresetAdmin(admin.ModelAdmin):
    list_display = ('name', 'monthly_investment', 'duration_years', 'risk_level', 'is_active')
    search_fields = ('name', 'description')
    list_filter = ('risk_level', 'is_active')
    fieldsets = (
        ('ข้อมูลพื้นฐาน', {
            'fields': ('name', 'description', 'is_active'),
        }),
        ('พารามิเตอร์แผน', {
            'fields': ('monthly_investment', 'duration_years', 'target_amount', 'expected_return', 'risk_level'),
        }),
        ('หุ้นที่เลือก', {
            'fields': ('selected_stocks',),
        }),
    )

@admin.register(UserInvestmentRecord)
class UserInvestmentRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'month', 'amount_invested', 'created_at')
    search_fields = ('user__username', 'notes')
    list_filter = ('month', 'user')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('ข้อมูลการลงทุน', {
            'fields': ('user', 'month', 'amount_invested'),
        }),
        ('หมายเหตุและวันที่', {
            'fields': ('notes', 'created_at', 'updated_at'),
        }),
    )


@admin.register(GAResultSnapshot)
class GAResultSnapshotAdmin(admin.ModelAdmin):
    list_display = ('user', 'saved_at', 'expected_return', 'sharpe_ratio', 'final_portfolio_value')
    search_fields = ('user__username',)
    list_filter = ('saved_at', 'user')
    readonly_fields = ('saved_at',)