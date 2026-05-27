from django.contrib import admin, messages
from django.utils.html import format_html
import yfinance as yf
import logging
import concurrent.futures
from .models import Stock, UserPlan

logger = logging.getLogger(__name__)

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'display_last_price', 'display_change', 'display_percent_change', 'is_set50', 'updated_at')
    list_display_links = ('symbol',)
    search_fields = ('symbol',)
    list_filter = ('is_set50',)
    ordering = ('-is_set50', 'symbol')
    list_per_page = 30
    actions = ['update_stock_prices']
    actions_on_top = True
    save_on_top = True
    show_full_result_count = True

    # 2. ย้ายฟังก์ชันอัปเดตราคามาไว้ใน Class นี้เลย
    @admin.action(description='อัปเดตราคาหุ้นจาก Yahoo Finance')
    def update_stock_prices(self, request, queryset):
        for stock in queryset:
            self._fetch_update(stock)

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
    def settrade_style_dashboard(self, obj):
        if obj.last_price is None or obj.last_price == 0:
            return format_html(
                '<div class="stock-live-card stock-live-card--empty">'
                '<div class="stock-live-card__title">{}</div>'
                '<div class="stock-live-card__note">{}</div>'
                '</div>',
                'Stock Live Quote',
                'ไม่มีข้อมูลราคาเรียลไทม์ ให้เลือก Action หรือกดแก้ไขเพื่อโหลดข้อมูลล่าสุด'
            )

        if obj.change > 0:
            card_type = 'stock-live-card--positive'
            icon = '▲'
            sign = '+'
        elif obj.change < 0:
            card_type = 'stock-live-card--negative'
            icon = '▼'
            sign = ''
        else:
            card_type = 'stock-live-card--neutral'
            icon = '-'
            sign = ''

        formatted_last_price = f"{obj.last_price:,.2f}"
        formatted_change = f"{obj.change:,.2f}"
        formatted_percent = f"{obj.percent_change:,.2f}%"

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
        color = "green" if obj.change > 0 else "red" if obj.change < 0 else "black"
        symbol = "+" if obj.change > 0 else ""
        formatted_change = f"{obj.change:.2f}"
        return format_html('<span style="color: {}; font-weight: bold;">{}{}</span>', color, symbol, formatted_change)
    display_change.short_description = "เปลี่ยนแปลง"

    def display_percent_change(self, obj):
        color = "green" if obj.percent_change > 0 else "red" if obj.percent_change < 0 else "black"
        symbol = "+" if obj.percent_change > 0 else ""
        formatted_pct = f"{obj.percent_change:.2f}"
        return format_html('<span style="color: {}; font-weight: bold;">{}{}%</span>', color, symbol, formatted_pct)
    display_percent_change.short_description = "% เปลี่ยนแปลง"

    def display_last_price(self, obj):
        formatted_price = f"{obj.last_price:,.2f}"
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
            hist = data.history(period="2d")
            if len(hist) >= 2:
                prev_close = hist['Close'].iloc[0]
                last_price = hist['Close'].iloc[1]
                change = last_price - prev_close
                pct_change = (change / prev_close) * 100

                stock.last_price = float(round(float(last_price), 2))
                stock.change = float(round(float(change), 2))
                stock.percent_change = float(round(float(pct_change), 2))
                stock.save()
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
    list_display = ('user', 'monthly_investment', 'duration_years', 'target_amount')
    search_fields = ('user__username',) 
    list_filter = ('duration_years',) 