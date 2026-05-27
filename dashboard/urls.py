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
]