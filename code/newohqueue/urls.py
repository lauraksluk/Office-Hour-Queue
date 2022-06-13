"""newohqueue URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from ohq import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.base, name='home'),
    path('login', views.login_page, name='login'),
    path('logout', auth_views.logout_then_login, name='logout'),
    path('manage', views.manage_page, name='manage'),
    path('upload-instructors-list', views.upload_file_action, name='upload-instructors-list'),
    path('loginoauth', views.oauth_page, name='oauth'),
    path('oauth/', include('social_django.urls', namespace='social'), name='oauthLogin'),
    path('register', views.register_page, name='register'),
    path('courses', views.courses_page, name='courses'),
    path('role-redirect/<int:queue_id>', views.role_redirect_action, name='role-redirect'),
    path('instructor/<int:queue_id>', views.instructor_action, name='instructor'),
    path('student/<int:queue_id>', views.student_action, name='home'),
    path('ohq/waiting-questions', views.waiting_questions_json),
    path('ohq/waiting-questions-count', views.waiting_questions_count_json),
    path('add_question/<int:queue_id>', views.add_question, name='add_question'),
    path('remove_question/<int:queue_id>', views.remove_question, name='remove_question'),
    path('ohq/student_current_position', views.student_current_position_json),
    path('ohq/assign_student_from_top_of_queue', views.assign_question_from_top_of_queue_json),
    path('ohq/queue-status', views.queue_status_json),
    path('ohq/set-queue-status', views.set_queue_status),
    path('ohq/add-announcement', views.add_announcement),
    path('ohq/get-announcements', views.get_announcements_json),
    path('ohq/assign_student_from_list', views.assign_question_from_list),
    path('ohq/get-assigned-question', views.get_assigned_question_json),
    path('ohq/finish-current-question', views.finish_current_question),
    path('pin_course/<int:queue_id>', views.pin_course, name='pin_course'),
    path('ohq/instruct-remove-question', views.instruct_remove_question),
    path('ohq/end_office_hour_session', views.end_office_hour_session),
    path('ohq/send_private_message', views.send_private_message),
    path('ohq/send_remove_reason_message', views.send_remove_reason_message),
    path('ohq/check_if_assigned', views.check_if_assigned),
    path('statistics/<int:queue_id>', views.statistics_action, name='statistics'),
]
