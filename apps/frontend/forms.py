from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from apps.backend.models import Profile, Category


class AuthForm(forms.Form):
	username = forms.CharField(
		max_length=32,
		required=True,
		widget=forms.TextInput(
			attrs={
				"type": "text",
				"placeholder": "Логин",
			}
		),
		label=""
	)

	password = forms.CharField(
		max_length=32,
		required=True,
		widget=forms.PasswordInput(
			attrs={
				"type": "password",
				"placeholder": "Пароль",
			}
		),
		label=""
	)


class ExtendedRegisterForm(UserCreationForm):
	username = forms.CharField(
		min_length=5,
		max_length=32,
		required=True,
		widget=forms.TextInput(
			attrs={
				"placeholder": "Логин",
			}
		),
		label=""
	)

	password1 = forms.CharField(
		widget=forms.PasswordInput(
			attrs={
				"placeholder": "Пароль",
			}
		),
		label=""
	)

	password2 = forms.CharField(
		widget=forms.PasswordInput(
			attrs={
				"placeholder": "Повторите пароль",
			}
		),
		label=""
	)

	email = forms.CharField(
		max_length=64,
		required=True,
		widget=forms.EmailInput(
			attrs={
				"placeholder": "Почта",
			}
		),
		label=""
	)

	full_name = forms.CharField(
		max_length=128,
		required=True,
		widget=forms.TextInput(
			attrs={
				"placeholder": "ФИО"
			}
		)
	)

	def clean(self):
		email = self.cleaned_data["email"].lower()
		new = User.objects.filter(email=email)
		if new.count():
			raise ValidationError("Ошибка: данный емейл уже есть")

		username = self.cleaned_data["username"].lower()
		new = User.objects.filter(username=username)
		if new.count():
			raise ValidationError("Ошибка: данный пользователь уже есть")

	class Meta:
		model = User
		fields = ("username", "full_name", "email", "password1", "password2",)


class ConfirmEmail(forms.Form):
	def __init__(self, *args, **kwargs):
		self.request = kwargs.pop("request")
		super(ConfirmEmail, self).__init__(*args, **kwargs)

	code = forms.CharField(
		min_length=6,
		max_length=6,
		required=True,
		widget=forms.TextInput(
			attrs={
				"placeholder": "Код"
			}
		),
		label=""
	)

	def clean(self):
		obj = Profile.objects.filter(user=self.request.user).first()
		if not str(obj.verify_code) == str(self.cleaned_data["code"]):
			raise ValidationError("Ошибка: Неверный код")


class UserPasswordResetForm(PasswordResetForm):
	def __init__(self, *args, **kwargs):
		super(UserPasswordResetForm, self).__init__(*args, **kwargs)

	email = forms.EmailField(
		label="",
		widget=forms.EmailInput(
			attrs={
				"placeholder": "Почта",
			}
		)
	)


class ForgotConfirm(forms.Form):
	def __init__(self, *args, **kwargs):
		self.request = kwargs.pop("request")
		super(ForgotConfirm, self).__init__(*args, **kwargs)

	email = forms.CharField(
		max_length=64,
		required=True,
		widget=forms.EmailInput(
			attrs={
				"placeholder": "Email"
			}
		),
		label=""
	)

	code = forms.CharField(
		min_length=6,
		max_length=6,
		required=True,
		widget=forms.TextInput(
			attrs={
				"placeholder": "Код"
			}
		),
		label=""
	)

	def clean(self):
		obj = Profile.objects.filter(email=self.cleaned_data["email"]).first()
		if not str(obj.recover_code) == str(self.cleaned_data["code"]):
			raise ValidationError("Ошибка: Неверный код")


class NewAd(forms.Form):
	title = forms.CharField(
		max_length=128,
		required=True,
		widget=forms.TextInput(
			attrs={
				"type": "text",
				"placeholder": "Название",
			}
		),
		label=""
	)

	price = forms.IntegerField(
		min_value=0,
		required=True,
		widget=forms.NumberInput(
			attrs={
				"placeholder": "Цена"
			}
		),
		label=""
	)

	description = forms.CharField(
		max_length=4096,
		required=True,
		widget=forms.Textarea(
			attrs={
				"placeholder": "Описание",
			}
		),
		label=""
	)

	category = forms.ModelChoiceField(
		queryset=Category.objects.all(),
		required=True,
		label="Категория"
	)


class EditAd(forms.Form):
	title = forms.CharField(
		max_length=128,
		required=False,
		widget=forms.TextInput(
			attrs={
				"type": "text",
				"placeholder": "Название",
			}
		),
		label=""
	)

	price = forms.IntegerField(
		min_value=0,
		required=False,
		widget=forms.NumberInput(
			attrs={
				"placeholder": "Цена"
			}
		),
		label=""
	)

	description = forms.CharField(
		max_length=4096,
		required=False,
		widget=forms.Textarea(
			attrs={
				"placeholder": "Описание",
			}
		),
		label=""
	)

	category = forms.ModelChoiceField(
		queryset=Category.objects.all(),
		required=False,
		label="Категория"
	)


class EditFullName(forms.Form):
	full_name_new = forms.CharField(
		max_length=128,
		required=True,
		widget=forms.TextInput(
			attrs={
				"placeholder": "Новое ФИО",
			}
		),
		label=""
	)


class NewReview(forms.Form):
	mark = forms.IntegerField(
		min_value=1,
		max_value=5,
		required=True,
		widget=forms.NumberInput(
			attrs={
				"placeholder": "Оценка"
			}
		),
		label=""
	)

	text = forms.CharField(
		max_length=4096,
		required=True,
		widget=forms.Textarea(
			attrs={
				"placeholder": "Текст отзыва",
			}
		),
		label=""
	)


class EditReview(forms.Form):
	mark = forms.IntegerField(
		min_value=1,
		max_value=5,
		required=False,
		widget=forms.NumberInput(
			attrs={
				"placeholder": "Оценка"
			}
		),
		label=""
	)

	text = forms.CharField(
		max_length=4096,
		required=False,
		widget=forms.Textarea(
			attrs={
				"placeholder": "Текст отзыва",
			}
		),
		label=""
	)


class EditCategory(forms.Form):
	categories = forms.ModelMultipleChoiceField(
		queryset=Category.objects.all(),
		widget=forms.CheckboxSelectMultiple(),
		required=False,
		label="Категории"
	)
