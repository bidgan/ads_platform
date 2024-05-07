from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import User


# Категория
class Category(models.Model):
	title = models.CharField(verbose_name="Наименование", max_length=64)

	class Meta:
		verbose_name = "Категория"
		verbose_name_plural = "Категории"

	def __str__(self):
		return self.title


# Профиль
class Profile(models.Model):
	user = models.OneToOneField(User, verbose_name="Пользователь", on_delete=models.CASCADE)
	email = models.CharField(verbose_name="Почта", max_length=64, blank=True)
	full_name = models.CharField(verbose_name="Имя", max_length=128, blank=True)
	is_confirmed = models.BooleanField(verbose_name="Подтверждено", default=False)
	is_avatar = models.BooleanField(verbose_name="Есть аватарка", default=False)
	verify_code = models.CharField(verbose_name="Код подтверждения", max_length=6, blank=True)
	code_timeout = models.CharField(verbose_name="Таймаут отправки кода", max_length=32)
	categories = models.ManyToManyField(Category, verbose_name="Категории", blank=True)
	updated_at = models.DateTimeField(verbose_name="Изменено", editable=False, auto_now=True)
	created_at = models.DateTimeField(verbose_name="Создано", editable=False, auto_now_add=True)

	class Meta:
		verbose_name = "Профиль"
		verbose_name_plural = "Профили"

	def __str__(self):
		return self.user.username


# Отзыв
class Review(models.Model):
	identity = models.CharField(verbose_name="Идентификатор", max_length=32, null=True)
	user = models.OneToOneField(User, verbose_name="Пользователь", related_name="user_review", on_delete=models.CASCADE)
	mark = models.IntegerField(verbose_name="Оценка", validators=[MinValueValidator(1), MaxValueValidator(5)])
	text = models.TextField(verbose_name="Текст отзыва", max_length=4096)
	reviewer = models.OneToOneField(User, verbose_name="Автор", related_name="reviewer_review", on_delete=models.SET_NULL, null=True)
	is_photo_sent = models.BooleanField(verbose_name="Фото отправлено", default=False)
	num_photos = models.IntegerField(verbose_name="Количество загруженных фото", default=0)
	updated_at = models.DateTimeField(verbose_name="Изменено", editable=False, auto_now=True)
	created_at = models.DateTimeField(verbose_name="Создано", editable=False, auto_now_add=True)

	class Meta:
		verbose_name = "Отзыв"
		verbose_name_plural = "Отзывы"

	def __str__(self):
		return f"{self.user} ~ {self.pk}"


# Объявление
class Advertisement(models.Model):
	identity = models.CharField(verbose_name="Идентификатор", max_length=32, null=True)
	title = models.CharField(verbose_name="Наименование", max_length=128)
	description = models.TextField(verbose_name="Описание", max_length=4096)
	category = models.ForeignKey(Category, verbose_name="Категория", null=True, on_delete=models.DO_NOTHING)
	price = models.IntegerField(verbose_name="Цена")
	seller = models.ForeignKey(User, verbose_name="Продавец", on_delete=models.CASCADE)
	num_photos = models.IntegerField(verbose_name="Количество загруженных фото", default=0)
	is_photo_sent = models.BooleanField(verbose_name="Фото отправлено", default=False)
	is_visible = models.BooleanField(verbose_name="Объявление открыто", default=False)
	updated_at = models.DateTimeField(verbose_name="Изменено", editable=False, auto_now=True)
	created_at = models.DateTimeField(verbose_name="Создано", editable=False, auto_now_add=True)

	class Meta:
		verbose_name = "Объявление"
		verbose_name_plural = "Объявления"

	def __str__(self):
		return f"{self.title} ~ {self.seller}"


# Диалог
class Dialog(models.Model):
	user1 = models.ForeignKey(User, verbose_name="Пользователь 1", related_name="dialog_user1", on_delete=models.CASCADE)
	user2 = models.ForeignKey(User, verbose_name="Пользователь 2", related_name="dialog_user2", on_delete=models.CASCADE)

	class Meta:
		verbose_name = "Диалог"
		verbose_name_plural = "Диалоги"

	def __str__(self):
		return f"Диалог {self.user1.username} и {self.user2.username}"

	def get_messages(self):
		return Message.objects.filter(dialog=self)


# Сообщение
class Message(models.Model):
	dialog = models.ForeignKey(Dialog, verbose_name="Диалог", on_delete=models.CASCADE)
	sender = models.ForeignKey(User, verbose_name="Отправитель", on_delete=models.CASCADE)
	message = models.TextField(verbose_name="Текст сообщения", max_length=1024)
	created_at = models.DateTimeField(verbose_name="Создано", editable=False, auto_now_add=True)

	class Meta:
		verbose_name = "Сообщение"
		verbose_name_plural = "Сообщения"

	def __str__(self):
		return f"Сообщение в диалоге {self.dialog.user1.username} и {self.dialog.user2.username}"
