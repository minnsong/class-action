from django import forms

STUDENT = [
	('Amy', 'Amy'),
	('Bob', 'Bob'),
	('Cal', 'Cal'),
]

class AddDropForm(forms.Form):
	chosen_student = forms.ChoiceField(
		required=False,
		label='',
		widget=forms.RadioSelect,
		choices=[],
	)	

class LoginForm(forms.Form):
	username = forms.CharField(label='Your name', max_length=32)
	password = forms.CharField(label='Password', max_length=32, widget=forms.PasswordInput)

class RegisterForm(forms.Form):
	student = forms.MultipleChoiceField(
		required=False,
		widget=forms.CheckboxSelectMultiple,
		choices=[],
	)
	
