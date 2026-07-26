from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.generic import UpdateView
from django.template.loader import render_to_string
from .models import Stock, UserPlan, UserProfile, UserInvestmentRecord, DCAPreset, GAResultSnapshot
from .services import build_dca_projection, normalize_selected_stocks
from .tasks import optimize_portfolio_task
from .optimizers import EqualWeightOptimizer, GAOptimizer

try:
    from weasyprint import HTML
except Exception:
    HTML = None
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
import json
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors

@login_required
def dashboard_view(request):
    plan, created = UserPlan.objects.get_or_create(user=request.user)
    all_stocks = Stock.objects.all().order_by('symbol')
    
    if request.method == 'POST' and 'selected_stocks' in request.POST:
        selected_assets = normalize_selected_stocks(
            ",".join(request.POST.getlist('selected_stocks'))
        )
        plan.selected_stocks = ",".join(selected_assets)
        plan.save()
    else:
        selected_assets = normalize_selected_stocks(plan.selected_stocks)

    ga_optimizer = GAOptimizer()
    equal_weight_optimizer = EqualWeightOptimizer()

    ga_results = ga_optimizer.optimize([type('StockRef', (), {'symbol': s})() for s in selected_assets], plan.target_amount)
    baseline_results = equal_weight_optimizer.optimize([type('StockRef', (), {'symbol': s})() for s in selected_assets], plan.target_amount)
    
    # 2. จัดรูปแบบสัดส่วนน้ำหนักสำหรับแสดงผล
    weights_display = []
    for stock, weight in ga_results['weights'].items():
        weights_display.append({'symbol': stock, 'percent': round(weight * 100, 1)})
        
    projection = build_dca_projection(
        monthly_investment=plan.monthly_investment,
        duration_years=plan.duration_years,
        target_amount=plan.target_amount,
        expected_return=ga_results['expected_return'],
    )
    chart_labels = projection['chart_labels']
    chart_data = projection['chart_data']
    current_value = projection['final_portfolio_value']
    is_target_reached = projection['is_target_reached']
    target_message = projection['target_message']

    context = {
        'set50_stocks': all_stocks,
        'selected_assets': selected_assets,
        'total_return_percent': f"{ga_results['expected_return']*100:.2f}%",
        'baseline_weights': baseline_results,
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
        'target_message': target_message,
        
        # ข้อมูล GA ที่บันทึกไว้
        'saved_ga_available': bool(plan.last_optimized_weights),
        'saved_ga_weights': plan.last_optimized_weights or {},
        'saved_ga_return': f"{plan.last_expected_return*100:.2f}%" if plan.last_expected_return is not None else None,
        'saved_ga_sharpe': f"{plan.last_sharpe_ratio:.2f}" if plan.last_sharpe_ratio is not None else None,
        'saved_ga_time': plan.updated_at if plan.last_optimized_weights else None,
        'saved_ga_chart_labels': json.dumps(plan.last_chart_labels or []),
        'saved_ga_chart_data': json.dumps(plan.last_chart_data or []),
    }
    return render(request, 'dashboard/index.html', context)

@login_required
def update_investment(request):
    if request.method == 'POST':
        plan = UserPlan.objects.get(user=request.user)
        try:
            monthly_raw = request.POST.get('monthly_investment_input', '').strip()
            if monthly_raw:
                plan.monthly_investment = Decimal(monthly_raw.replace(',', ''))

            duration_raw = request.POST.get('duration_years_input', '').strip()
            if duration_raw:
                plan.duration_years = max(1, int(duration_raw))

            target_raw = request.POST.get('target_amount_input', '').strip()
            if target_raw:
                plan.target_amount = Decimal(target_raw.replace(',', ''))

            if plan.monthly_investment <= 0 or plan.target_amount <= 0:
                raise InvalidOperation('Values must be positive')

            plan.save()
            task = optimize_portfolio_task.delay(plan.id)
            messages.success(request, 'กำลังประมวลผล GA ในพื้นหลัง กรุณารอซักครู่')
            return redirect('dashboard')
        except (InvalidOperation, ValueError) as e:
            messages.error(request, 'ข้อมูลที่ป้อนไม่ถูกต้อง กรุณาตรวจสอบแล้วส่งใหม่')
    return redirect('dashboard')


@login_required
def start_optimization(request, plan_id):
    """Dispatch GA optimization to a background task and return immediately."""
    try:
        plan = UserPlan.objects.get(id=plan_id, user=request.user)
    except UserPlan.DoesNotExist:
        return JsonResponse({'error': 'Plan not found'}, status=404)

    task = optimize_portfolio_task.delay(plan.id)
    return JsonResponse({'task_id': task.id, 'status': 'Processing'})


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

# ==========================================
# ฟีเจอร์ใหม่: โปรไฟล์ผู้ใช้
# ==========================================

@login_required
def profile_view(request):
    """ดูโปรไฟล์ผู้ใช้"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'dashboard/profile.html', {'profile': profile})

@login_required
def profile_edit_view(request):
    """แก้ไขโปรไฟล์ผู้ใช้"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    user = request.user
    
    if request.method == 'POST':
        # แก้ไขข้อมูลส่วนตัว
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        user.save()
        
        # แก้ไขข้อมูล profile
        profile.phone = request.POST.get('phone', '').strip()
        profile.bio = request.POST.get('bio', '').strip()
        profile.preferred_language = request.POST.get('preferred_language', 'th')
        profile.save()
        
        messages.success(request, 'บันทึกการเปลี่ยนแปลงสำเร็จแล้ว')
        return redirect('profile')
    
    context = {
        'profile': profile,
    }
    return render(request, 'dashboard/profile_edit.html', context)

@login_required
def password_change_view(request):
    """เปลี่ยนรหัสผ่าน"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password', '')
        new_password1 = request.POST.get('new_password1', '')
        new_password2 = request.POST.get('new_password2', '')
        
        if not request.user.check_password(old_password):
            messages.error(request, 'รหัสผ่านเก่าไม่ถูกต้อง')
        elif new_password1 != new_password2:
            messages.error(request, 'รหัสผ่านใหม่ไม่ตรงกัน')
        elif len(new_password1) < 8:
            messages.error(request, 'รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร')
        else:
            request.user.set_password(new_password1)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'เปลี่ยนรหัสผ่านสำเร็จแล้ว')
            return redirect('profile')
    
    return render(request, 'dashboard/password_change.html')

# ==========================================
# ฟีเจอร์ใหม่: บันทึกการลงทุน
# ==========================================

@login_required
def investment_records_view(request):
    """ดูบันทึกการลงทุน"""
    records = UserInvestmentRecord.objects.filter(user=request.user).order_by('-month')

    # สรุปสถิติสำหรับแสดงผล (รวม, จำนวน, ค่าเฉลี่ยต่อเดือน)
    total_records = records.count()
    # จำนวนรวมเป็น Decimal -> แปลงเป็นตัวเลขก่อนจัดรูปแบบ
    total_invested = sum([r.amount_invested for r in records]) if total_records > 0 else 0
    try:
        average_per_month = (total_invested / total_records) if total_records > 0 else 0
    except Exception:
        average_per_month = 0

    context = {
        'records': records,
        'total_invested': f"{int(total_invested):,}",
        'average_per_month': f"{int(average_per_month):,}",
    }
    return render(request, 'dashboard/investment_records.html', context)

@login_required
def add_investment_record_view(request):
    """เพิ่มบันทึกการลงทุน"""
    context = {
        'month_value': datetime.now().strftime('%Y-%m'),
        'amount_invested': '',
        'notes': '',
    }

    if request.method == 'POST':
        month_str = request.POST.get('month', '').strip()
        amount_str = request.POST.get('amount_invested', '').replace(',', '').strip()
        notes = request.POST.get('notes', '').strip()

        context.update({
            'month_value': month_str or datetime.now().strftime('%Y-%m'),
            'amount_invested': request.POST.get('amount_invested', ''),
            'notes': notes,
        })

        if not month_str:
            messages.error(request, 'กรุณาเลือกรายเดือนการลงทุน')
        elif not amount_str:
            messages.error(request, 'กรุณากรอกจำนวนเงินที่ลงทุน')
        else:
            try:
                month = datetime.strptime(month_str, '%Y-%m').date()
                amount = Decimal(amount_str)
                if amount <= 0:
                    raise InvalidOperation('Amount must be greater than zero')

                record, created = UserInvestmentRecord.objects.get_or_create(
                    user=request.user,
                    month=month,
                    defaults={'amount_invested': amount, 'notes': notes}
                )
                if not created:
                    record.amount_invested = amount
                    record.notes = notes
                    record.save()

                messages.success(request, 'บันทึกการลงทุนสำเร็จแล้ว')
                return redirect('investment_records')
            except ValueError:
                messages.error(request, 'รูปแบบเดือนไม่ถูกต้อง โปรดเลือกเดือนใหม่')
            except InvalidOperation:
                messages.error(request, 'จำนวนเงินต้องเป็นตัวเลขมากกว่า 0')

    return render(request, 'dashboard/add_investment_record.html', context)


@login_required
def ga_history_view(request):
    """แสดงประวัติการบันทึกผล GA ของผู้ใช้"""
    snapshots = GAResultSnapshot.objects.filter(user=request.user).order_by('-saved_at')
    return render(request, 'dashboard/ga_history.html', {'snapshots': snapshots})


@login_required
def ga_history_detail_view(request, pk):
    """แสดงรายละเอียด snapshot เดียว (กราฟ + น้ำหนักหุ้น)"""
    snapshot = get_object_or_404(GAResultSnapshot, pk=pk, user=request.user)

    # prepare chart data
    chart_labels = snapshot.chart_labels or []
    chart_data = snapshot.chart_data or []

    # prepare weights for display (list of {symbol, pct})
    weights = []
    if snapshot.weights:
        for sym, v in snapshot.weights.items():
            try:
                pct = float(v) * 100
            except Exception:
                pct = v
            weights.append({'symbol': sym, 'percent': pct})

    context = {
        'snapshot': snapshot,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'weights': weights,
    }
    return render(request, 'dashboard/ga_snapshot_detail.html', context)


@login_required
def download_plan_pdf(request, plan_id):
    plan = get_object_or_404(UserPlan, id=plan_id, user=request.user)
    html_string = render_to_string('dashboard/pdf_template.html', {'plan': plan})

    if HTML is None:
        response = HttpResponse(html_string, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="dca_plan_{plan.id}.html"'
        return response

    pdf_file = HTML(string=html_string).write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="dca_plan_{plan.id}.pdf"'
    return response

# ==========================================
# ฟีเจอร์ใหม่: สถิติการลงทุน
# ==========================================

@login_required
def statistics_view(request):
    """ดูสถิติการลงทุนของผู้ใช้"""
    plan = UserPlan.objects.get(user=request.user)
    records = UserInvestmentRecord.objects.filter(user=request.user)
    
    # คำนวณสถิติ
    total_invested = sum([r.amount_invested for r in records])
    total_records = records.count()
    average_per_month = total_invested / total_records if total_records > 0 else 0
    
    # ข้อมูลสำหรับกราฟ
    chart_data = []
    for record in records.order_by('month'):
        chart_data.append({
            'month': record.month.strftime('%b %Y'),
            'amount': float(record.amount_invested)
        })
    
    context = {
        'plan': plan,
        'total_invested': f"{int(total_invested):,}",
        'total_records': total_records,
        'average_per_month': f"{int(average_per_month):,}",
        'chart_data': json.dumps(chart_data),
    }
    return render(request, 'dashboard/statistics.html', context)

# ==========================================
# ฟีเจอร์ใหม่: แผน DCA สำเร็จรูป
# ==========================================

@login_required
def preset_plans_view(request):
    """ดูแผน DCA สำเร็จรูป"""
    presets = DCAPreset.objects.filter(is_active=True)
    
    # แปลง selected_stocks เป็น list เพื่อให้ template ใช้ได้ง่ายขึ้น
    for preset in presets:
        preset.stocks_list = [s.strip() for s in preset.selected_stocks.split(',') if s.strip()]
    
    context = {
        'presets': presets,
    }
    return render(request, 'dashboard/preset_plans.html', context)

@login_required
def apply_preset_plan_view(request, plan_id):
    """นำแผนไปใช้"""
    try:
        preset = DCAPreset.objects.get(id=plan_id, is_active=True)
        user_plan = UserPlan.objects.get(user=request.user)
        
        user_plan.monthly_investment = preset.monthly_investment
        user_plan.duration_years = preset.duration_years
        user_plan.target_amount = preset.target_amount
        user_plan.selected_stocks = preset.selected_stocks
        user_plan.save()
        
        messages.success(request, f'นำแผน "{preset.name}" ไปใช้สำเร็จแล้ว')
        return redirect('dashboard')
    except DCAPreset.DoesNotExist:
        messages.error(request, 'ไม่พบแผนที่ระบุ')
        return redirect('preset_plans')

# ==========================================
# ฟีเจอร์ใหม่: ส่งออก PDF แบบปรับปรุง
# ==========================================

@login_required
def export_plan_pdf_view(request):
    """ส่งออกแผนการลงทุนเป็น PDF"""
    plan = UserPlan.objects.get(user=request.user)
    
    # สร้าง PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # ชื่อเอกสาร
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#047857'),
        spaceAfter=30,
        alignment=1  # Center
    )
    elements.append(Paragraph('แผนการลงทุน DCA', title_style))
    elements.append(Spacer(1, 12))
    
    # ข้อมูลผู้ใช้
    user_info = [
        ['ชื่อผู้ใช้:', request.user.username],
        ['ชื่อ-สกุล:', f"{request.user.first_name} {request.user.last_name}"],
        ['อีเมล:', request.user.email],
        ['วันที่สร้างเอกสาร:', datetime.now().strftime('%d/%m/%Y %H:%M')],
    ]
    user_table = Table(user_info, colWidths=[2*inch, 4*inch])
    user_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E0F2FE')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(user_table)
    elements.append(Spacer(1, 24))
    
    # ข้อมูลแผน
    elements.append(Paragraph('ข้อมูลแผนการลงทุน', styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    plan_info = [
        ['เงินลงทุนรายเดือน:', f"{int(plan.monthly_investment):,} บาท"],
        ['ระยะเวลา:', f"{plan.duration_years} ปี"],
        ['เป้าหมายทางการเงิน:', f"{int(plan.target_amount):,} บาท"],
        ['หุ้นที่เลือก:', plan.selected_stocks],
    ]
    plan_table = Table(plan_info, colWidths=[2*inch, 4*inch])
    plan_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F0FDF4')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(plan_table)
    
    # สร้าง PDF
    doc.build(elements)
    buffer.seek(0)
    
    return FileResponse(buffer, as_attachment=True, filename=f'DCA_Plan_{datetime.now().strftime("%Y%m%d")}.pdf')