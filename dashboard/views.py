from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Stock, UserPlan
from .ga_optimizer import run_genetic_algorithm
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib import messages
from decimal import Decimal, InvalidOperation

@login_required
def dashboard_view(request):
    plan, created = UserPlan.objects.get_or_create(user=request.user)
    all_stocks = Stock.objects.all().order_by('symbol')
    
    if request.method == 'POST' and 'selected_stocks' in request.POST:
        selected_assets = [s.strip() for s in request.POST.getlist('selected_stocks') if s.strip()]
        plan.selected_stocks = ",".join(selected_assets)
        plan.save()
    else:
        selected_assets = [s.strip() for s in plan.selected_stocks.split(',') if s.strip()]

    # 1. รัน GA เพื่อหาน้ำหนักที่เหมาะสม
    ga_results = run_genetic_algorithm(assets=selected_assets)
    
    # 2. จัดรูปแบบสัดส่วนน้ำหนักสำหรับแสดงผล
    weights_display = []
    for stock, weight in ga_results['weights'].items():
        weights_display.append({'symbol': stock, 'percent': round(weight * 100, 1)})
        
    # 3. คำนวณมูลค่าพอร์ตในอนาคตเพื่อสร้างกราฟ Chart.js (สูตร Future Value of DCA)
    monthly_rate = ga_results['expected_return'] / 12
    monthly_inv = float(plan.monthly_investment)
    duration_months = plan.duration_years * 12
    
    chart_labels = []
    chart_data = []
    current_value = 0
    achievement_month = None
    target_amount_value = float(plan.target_amount)
    
    # คำนวณจุดแสดงผลรายปี
    for month in range(1, duration_months + 1):
        current_value = (current_value + monthly_inv) * (1 + monthly_rate)
        if achievement_month is None and current_value >= target_amount_value:
            achievement_month = month
        if month % 12 == 0 or month == duration_months:
            chart_labels.append(f"ปีที่ {month//12}")
            chart_data.append(round(current_value, 2))
            
    # ตรวจสอบว่าถึงเป้าหมายหรือไม่
    is_target_reached = current_value >= target_amount_value
    if achievement_month is not None:
        achievement_year = ((achievement_month - 1) // 12) + 1
        achievement_quarter = ((achievement_month - 1) // 3) + 1
        target_message = f"คาดว่าจะบรรลุเป้าหมายในปีที่ {achievement_year} (ไตรมาสที่ {achievement_quarter})"
    else:
        target_message = "คาดว่าจะไม่ถึงเป้าหมายภายในระยะเวลาที่กำหนด"

    context = {
        'set50_stocks': all_stocks,
        'selected_assets': selected_assets,
        'total_return_percent': f"{ga_results['expected_return']*100:.2f}%",
        'sharpe_ratio': f"{ga_results['sharpe_ratio']:.2f}",
        'weights_display': sorted(weights_display, key=lambda x: x['percent'], reverse=True),
        
        # ข้อมูลฟอร์ม
        'monthly_investment': f"{int(plan.monthly_investment):,}",
        'monthly_investment_raw': plan.monthly_investment,
        'duration_years': plan.duration_years,
        'target_amount_raw': plan.target_amount,
        'target_amount': f"{int(plan.target_amount):,}",
        
        # ข้อมูลกราฟ
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'final_portfolio_value': f"{int(current_value):,}",
        'is_target_reached': is_target_reached,
        'target_message': target_message
    }
    return render(request, 'dashboard/index.html', context)

@login_required
def update_investment(request):
    if request.method == 'POST':
        plan = UserPlan.objects.get(user=request.user)
        # รับค่าทั้งหมดที่ถูกส่งมาจากฟอร์มการแก้ไข และแปลงชนิดข้อมูลก่อนบันทึก
        try:
            monthly_raw = request.POST.get('monthly_investment_input', '').strip()
            if monthly_raw:
                monthly_clean = monthly_raw.replace(',', '')
                plan.monthly_investment = Decimal(monthly_clean)

            duration_raw = request.POST.get('duration_years_input', '').strip()
            if duration_raw:
                plan.duration_years = int(duration_raw)

            target_raw = request.POST.get('target_amount_input', '').strip()
            if target_raw:
                target_clean = target_raw.replace(',', '')
                plan.target_amount = Decimal(target_clean)

            plan.save()
        except (InvalidOperation, ValueError) as e:
            messages.error(request, 'ข้อมูลที่ป้อนไม่ถูกต้อง กรุณาตรวจสอบแล้วส่งใหม่')
    return redirect('dashboard')
def register_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p1 = request.POST.get('password')
        p2 = request.POST.get('confirm_password')
        
        # ตรวจสอบว่ากรอกรหัสผ่านตรงกันไหม
        if p1 != p2:
            messages.error(request, 'รหัสผ่านทั้งสองช่องไม่ตรงกัน กรุณาลองใหม่')
        # ตรวจสอบว่าชื่อผู้ใช้นี้ซ้ำกับในระบบไหม
        elif User.objects.filter(username=u).exists():
            messages.error(request, 'ชื่อผู้ใช้นี้มีในระบบแล้ว กรุณาใช้ชื่ออื่น')
        else:
            # สร้าง User ใหม่
            user = User.objects.create_user(username=u, password=p1)
            # สร้างแผนการลงทุนเปล่าๆ ให้ User คนนี้ทันที
            from .models import UserPlan
            UserPlan.objects.create(user=user)
            # พยายาม authenticate แล้วล็อกอินอัตโนมัติ
            auth_user = authenticate(username=u, password=p1)
            if auth_user is not None:
                login(request, auth_user)
                return redirect('dashboard')
            else:
                messages.error(request, 'บัญชีถูกสร้างแล้ว แต่ล็อกอินอัตโนมัติไม่สำเร็จ กรุณาล็อกอินด้วยตนเอง')
            
    return render(request, 'dashboard/register.html')    