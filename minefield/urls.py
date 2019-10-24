from django.urls import path

from . import views

app_name = 'minefield'
urlpatterns = [
	path('', views.index, name='index'),
	path('signin/<person_type>/', views.signin, name='signin'),
	path('signin/teacher/login/', views.login, name='login'),
	path('s/<student_name>/', views.show_questions_s, name='questions_s'),
	path('s/<student_name>/guess/', views.submit_guess_s, name='submit_guess_s'),
	path('s/<student_name>/guess/show/', views.show_guess, name='show_guess'),
	# path('s/<student_name>/guess/error/', views.show_error_s, name='error_s'),
	path('t/<teacher_name>/', views.init_class, name='init_class'),
	path('t/<teacher_name>/attendance/', views.take_attendance, name='attendance'),
	path('t/<teacher_name>/students/', views.show_students, name='show_students'),
	path('t/<teacher_name>/students/add/', views.add_student, name='add_student'),
	path('t/<teacher_name>/students/drop/', views.drop_student, name='drop_student'),
	path('t/<teacher_name>/teams/', views.show_teams, name='show_teams'),
	path('t/<teacher_name>/teams/rearrange/', views.rearrange_teams, name='rearrange_teams'),
	# path('t/<teacher_name>/questionnaire', views.show_master, name='master'),
	path('t/<teacher_name>/game/', views.show_game, name='game'),
	path('t/<teacher_name>/game/questions/', views.show_questions_t, name='questions_t'),
	path('t/<teacher_name>/game/guess/show/', views.show_guess, name='guess_class'),
	path('t/<teacher_name>/game/guess/do/', views.submit_guess_t, name='submit_guess_t'),
	path('t/<teacher_name>/game/guess/<hit_landmine>/', views.show_result, name='result'),
	path('t/<teacher_name>/game/discussion/', views.show_discussion, name='discussion'),
	path('t/<teacher_name>/game/score/', views.show_scoreboard, name='scoreboard'),
	path('t/<teacher_name>/master/', views.show_master, name='master'),
	path('t/<teacher_name>/master/update/', views.update_master, name='update_master')
]
