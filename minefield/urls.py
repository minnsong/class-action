from django.urls import path

from . import views

app_name = 'minefield'
urlpatterns = [
	path('', views.index, name='index'),
	path('signin/<person_type>/', views.signin, name='signin'),
	path('signin/teacher/login/', views.login, name='login'),
	path('s/<student_name>/', views.questionnaire, name='questionnaire'),
	path('s/<student_name>/guess/', views.guess, name='guess'),
	path('t/<teacher_name>/', views.init, name='init'),
	path('t/<teacher_name>/attendance/', views.take_attendance, name='attendance'),
	path('t/<teacher_name>/teams/', views.rearrange_teams, name='teams'),
]
