from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    # =========================
    # Authentication
    # =========================
    
    # Login Page
    path(
        '',
        auth_views.LoginView.as_view(
            template_name='dashboard/login.html',
            redirect_authenticated_user=True
        ),
        name='login'
    ),

    # Register Page 
    path(
        'register/',
        views.register_view,
        name='register'
    ),

    # Logout
    path(
        'logout/',
        auth_views.LogoutView.as_view(
            next_page='login'
        ),
        name='logout'
    ),

    # =========================
    # Dashboard
    # =========================
    
    # Main Dashboard (Require Login)
    path(
        'dashboard/',
        login_required(views.dashboard_view),
        name='dashboard'
    ),

    # Update Investment (Require Login)
    path(
        'update-investment/',
        login_required(views.update_investment),
        name='update_investment'
    ),

    # =========================
    # Profile Management
    # =========================
    
    # View Profile
    path(
        'profile/',
        login_required(views.profile_view),
        name='profile'
    ),
    
    # Edit Profile
    path(
        'profile/edit/',
        login_required(views.profile_edit_view),
        name='profile_edit'
    ),
    
    # Change Password
    path(
        'profile/change-password/',
        login_required(views.password_change_view),
        name='password_change'
    ),

    # =========================
    # Investment Records
    # =========================
    
    # View Investment Records
    path(
        'investment-records/',
        login_required(views.investment_records_view),
        name='investment_records'
    ),
    
    # Add Investment Record
    path(
        'investment-records/add/',
        login_required(views.add_investment_record_view),
        name='add_investment_record'
    ),

    # =========================
    # Statistics
    # =========================
    
    # View Statistics
    path(
        'statistics/',
        login_required(views.statistics_view),
        name='statistics'
    ),

    # =========================
    # DCA Preset Plans
    # =========================
    
    # View Preset Plans
    path(
        'preset-plans/',
        login_required(views.preset_plans_view),
        name='preset_plans'
    ),
    
    # Apply Preset Plan
    path(
        'preset-plans/<int:plan_id>/apply/',
        login_required(views.apply_preset_plan_view),
        name='apply_preset_plan'
    ),

    # GA History
    path(
        'ga-history/',
        login_required(views.ga_history_view),
        name='ga_history'
    ),
    path(
        'ga-history/<int:pk>/',
        login_required(views.ga_history_detail_view),
        name='ga_history_detail'
    ),

    # =========================
    # Export
    # =========================
    
    # Export Plan to PDF
    path(
        'export/plan-pdf/',
        login_required(views.export_plan_pdf_view),
        name='export_plan_pdf'
    ),
]