from django.urls import path

from . import views

app_name = 'minefield'
urlpatterns = [
	path('', views.index, name='index'),
	path('signin/<person_type>/', views.signin, name='signin'),
	path('signin/teacher/login/', views.login, name='login'),
	path('s/<student_name>/', views.show_questionnaire, name='questionnaire_student'),
	path('s/<student_name>/guess/', views.show_guess, name='show_guess'),
	path('t/<teacher_name>/', views.init_class, name='init_class'),
	path('t/<teacher_name>/attendance/', views.take_attendance, name='attendance'),
	path('t/<teacher_name>/students/', views.show_students, name='show_students'),
	path('t/<teacher_name>/teams/', views.rearrange_teams, name='teams'),
	path('c/questionnaire/', views.show_questionnaire_class, name='questionnaire_class'),
	path('c/guess/', views.show_guess, name='guess_class'),
	path('c/guess/<hit_landmine>/', views.score, name='score'),
]
