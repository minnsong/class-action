from django.urls import path

from . import views

app_name = 'minefield'
urlpatterns = [
	path('', views.index, name='index'),
	path('signin/<person_type>/', views.signin, name='signin'),
	path('signin/teacher/login/', views.login, name='login'),
	path('s/<student_name>/', views.questionnaire, name='questionnaire'),
	path('s/<student_name>/guess/', views.guess, name='guess'),
	path('t/<username>/', views.init, name='init'),
	path('t/<teacher_name>/register/', views.register, name='register'),
]
