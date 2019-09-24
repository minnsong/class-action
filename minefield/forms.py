from django import forms

class LoginForm(forms.Form):
	username = forms.CharField(label='Your name', max_length=32)
	password = forms.CharField(label='Password', max_length=32, widget=forms.PasswordInput)

class RegisterForm(forms.Form):
	students = forms.MultipleChoiceField(
		required=False,
		widget=forms.CheckboxSelectMultiple,
		choices=[],
	)
	
