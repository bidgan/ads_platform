import datetime
import logging

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.db.models import Avg, Q
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.backend.models import Profile, Advertisement, Review, Category, Dialog, Message
from apps.backend.views import send_mail, generate_code, generate_id, is_ajax, write_photo, delete_photo
from apps.frontend.forms import AuthForm, ConfirmEmail, UserPasswordResetForm, ExtendedRegisterForm, NewAd, \
	EditFullName, EditAd, NewReview, EditReview, EditCategory, EditDormitory
from main import settings
from main.settings import BASE_DIR


NAME = settings.NAME
DOMAIN = settings.DOMAIN
CODE_RESEND_TIMEOUT = int(settings.CODE_RESEND_TIMEOUT)

logging.basicConfig(
	level=logging.INFO,
	filename="frontend_views.log",
	filemode="a+",
	format="%(asctime)s %(levelname)s %(message)s"
)


def index_view(request):
	message = []
	ads, categories, my_categories = [], [], []
	try:
		if request.method == "POST":
			if is_ajax(request):
				try:
					if request.POST.getlist("categories[]", []):
						selected_categories = request.POST.getlist("categories[]", [])
						ads = Advertisement.objects.filter(
							is_visible=True,
							category__in=selected_categories,
							is_moderated=True).order_by("?")
						data = [
							{
								"identity": ad.identity,
								"title": ad.title,
								"price": ad.price,
								"updated_at": ad.updated_at
							} for ad in ads]
						data.insert(0, {"status": "success"})

						return JsonResponse(data, safe=False)
					elif request.POST.get("action"):
						if request.POST.get("action") == "search":
							ads = Advertisement.objects.filter(
								is_visible=True,
								title__icontains=request.POST.get("data"),
								is_moderated=True)
							data = [
								{
									"identity": ad.identity,
									"title": ad.title,
									"price": ad.price,
									"updated_at": ad.updated_at
								} for ad in ads]
							data.insert(0, {"status": "success"})

							return JsonResponse(data, safe=False)
					else:
						return JsonResponse({
							"status": "failed",
							"message": "Error"
						})

				except Exception as e:
					logging.error(f"{type(e).__name__}: {str(e)}")
					return JsonResponse(
						[{
							"status": "failed",
							"message": str(e.message) if str(
								type(e).__name__) == "ValidationError" else f"{type(e).__name__}: {str(e)}",
						}], safe=False
					)

		if request.user.is_authenticated:
			my_categories = request.user.profile.categories.all()
			ads = Advertisement.objects.filter(
				is_visible=True,
				category__in=my_categories,
				is_moderated=True).order_by("?")[:10]
			my_categories = [cat.pk for cat in my_categories]
		else:
			ads = Advertisement.objects.filter(
				is_visible=True,
				is_moderated=True).order_by("?")[:10]

		categories = Category.objects.filter().all()
	except Exception as e:
		logging.error(f"{type(e).__name__}: {str(e)}")
		message = ["False", f"{type(e).__name__}: {str(e)}"]

	return render(
		request,
		"index.html",
		{
			"ads": ads,
			"categories": categories,
			"my_categories": my_categories,
			"message": message,
		})


def account_view(request):
	if not request.user.is_authenticated:
		return redirect("/login")
	message = []
	try:
		if not request.user.profile.is_confirmed:
			return redirect("/confirm")
	except Exception as e:
		if str(e) == "User has no profile.":
			html = "Ошибка: Профиль не создан"
			return HttpResponse(html)
		logging.error(f"{type(e).__name__}: {str(e)}")
		message = ["False", f"{type(e).__name__}: {str(e)}"]

	profile = Profile.objects.filter(user=request.user).first()
	nickname = request.user.username
	full_name = profile.full_name
	dormitory = profile.dormitory
	is_avatar = profile.is_avatar
	ads = Advertisement.objects.filter(seller=request.user).all()
	categories = profile.categories.all()
	reviews = Review.objects.filter(user=request.user).all()
	# TODO: переписать, неэффективно
	rating = reviews.aggregate(avg_rating=Avg("mark"))["avg_rating"]
	if rating is None:
		rating = 0.0

	return render(
		request,
		"account/lk.html",
		{
			"nickname": nickname,
			"full_name": full_name,
			"dormitory": dormitory,
			"is_avatar": is_avatar,
			"ads": ads,
			"reviews": reviews,
			"rating": rating,
			"categories": categories,
			"message": message,
		}
	)


def other_account_view(request, profile_pk):
	user = User.objects.filter(username=profile_pk).first()
	if not user:
		raise Http404
	if request.method == "POST":
		if is_ajax(request):
			try:
				if request.POST.get("action") == "start_dialog":
					users = (request.user, user)
					dialog = Dialog.objects.filter(Q(user1__in=users) & Q(user2__in=users)).first()
					if not dialog:
						dialog = Dialog.objects.create(user1=request.user, user2=user)
						dialog.save()

					return JsonResponse(
						{
							"status": "success",
							"message": dialog.pk
						}
					)
			except Exception as e:
				logging.error(f"{type(e).__name__}: {str(e)}")
				return JsonResponse(
					[{
						"status": "failed",
						"message": str(e.message) if str(
							type(e).__name__) == "ValidationError" else f"{type(e).__name__}: {str(e)}",
					}], safe=False
				)
	message = []
	profile = user.profile
	nickname = user.username
	full_name = profile.full_name
	dormitory = profile.dormitory
	is_avatar = profile.is_avatar
	ads = Advertisement.objects.filter(
		seller=user,
		is_visible=True,
		is_moderated=True).all()
	reviews = Review.objects.filter(user=user).order_by("-created_at").all()
	# TODO: переписать, неэффективно
	rating = reviews.aggregate(avg_rating=Avg("mark"))["avg_rating"]
	if rating is None:
		rating = 0.0

	return render(
		request,
		"account/other_account.html",
		{
			"nickname": nickname,
			"full_name": full_name,
			"dormitory": dormitory,
			"is_avatar": is_avatar,
			"ads": ads,
			"reviews": reviews,
			"rating": rating,
			"message": message,
		}
	)


def register_view(request):
	if request.user.is_authenticated:
		return redirect("/account/")
	message = []
	form = ExtendedRegisterForm()
	if request.method == "POST":
		try:
			form = ExtendedRegisterForm(request.POST)
			if form.is_valid():
				email = form.cleaned_data.get("email")
				username = form.cleaned_data.get("username")
				raw_password = form.cleaned_data.get("password1")
				full_name = form.cleaned_data.get("full_name")

				code = generate_code()
				now = datetime.datetime.now()
				new_timeout = datetime.datetime.timestamp(now + datetime.timedelta(minutes=CODE_RESEND_TIMEOUT))

				subject = "Подтверждение e-mail"
				message = f"Здравствуйте, {username}\nПожалуйста, подтвердите свой e-mail, вставив данный код на " \
						  f"сайте {NAME}: {code}"
				try:
					send_mail(
						receiver=email,
						subject=subject,
						message=message
					)
					user = form.save()
					Profile.objects.create(
						user=user,
						full_name=full_name,
						email=email,
						is_confirmed=False,
						verify_code=code,
						code_timeout=new_timeout
					)
					user = authenticate(
						username=username,
						password=raw_password
					)
					login(request, user)
					return redirect("/confirm")
				except Exception as e:
					logging.error(f"{type(e).__name__}: {str(e)}")
					message = ["False", f"{type(e).__name__}: {str(e)}"]

		except Exception as e:
			logging.error(f"{type(e).__name__}: {str(e)}")
			message = ["False", f"{type(e).__name__}: {str(e)}"]

	return render(
		request,
		"account/register.html",
		{
			"form": form,
			"message": message,
		}
	)


def login_view(request):
	if request.user.is_authenticated:
		return redirect("/account/")
	message = []
	auth_form = AuthForm()
	if request.method == "POST":
		try:
			auth_form = AuthForm(request.POST)
			if auth_form.is_valid():
				username = auth_form.cleaned_data["username"]
				password = auth_form.cleaned_data["password"]
				user = authenticate(
					username=username,
					password=password
				)
				if user:
					if user.is_active:
						login(request, user)
						return redirect("/account/")
					else:
						auth_form.add_error("__all__", "Ошибка: аккаунт не активен")
				else:
					auth_form.add_error("__all__", "Ошибка: аккаунт не найден")
		except Exception as e:
			logging.error(f"{type(e).__name__}: {str(e)}")
			message = ["False", f"{type(e).__name__}: {str(e)}"]

	return render(
		request,
		"account/login.html",
		{
			"form": auth_form,
			"message": message,
		}
	)


def confirm_view(request):
	if not request.user.is_authenticated:
		return redirect("/")
	if request.user.profile.is_confirmed:
		return redirect("/account/")
	message = []
	form_confirm = ConfirmEmail(request=request)
	if request.method == "POST":
		try:
			if "btn_confirm_email" in request.POST:
				form_confirm = ConfirmEmail(request.POST, request=request)
				if form_confirm.is_valid():
					obj = Profile.objects.filter(user=request.user).first()
					obj.is_confirmed = True
					obj.save()
					return redirect("/account/")

			elif "btn_resend_email" in request.POST:
				obj = Profile.objects.filter(user=request.user).first()
				now = datetime.datetime.now()
				if float(obj.code_timeout) <= float(datetime.datetime.timestamp(now)):
					code = generate_code()
					new_timeout = datetime.datetime.timestamp(
						now + datetime.timedelta(minutes=CODE_RESEND_TIMEOUT))
					obj.verify_code = code
					obj.code_timeout = new_timeout
					obj.save()
					subject = "Подтверждение e-mail"
					msg = f"Здравствуйте, {obj.user}\nПожалуйста, подтвердите свой e-mail, вставив данный код на " \
						  f"сайте {NAME}: {code}"
					send_mail(
						subject=subject,
						message=msg,
						receiver=obj.email
					)
					message = ["True", "Код повторно отправлен вам на почту"]
				else:
					message = ["False", f"Подождите {CODE_RESEND_TIMEOUT} мин. с момента прошлой отправки"]
		except Exception as e:
			logging.error(f"{type(e).__name__}: {str(e)}")
			message = ["False", f"{type(e).__name__}: {str(e)}"]

	return render(
		request,
		"account/confirm.html",
		{
			"form_confirm": form_confirm,
			"message": message
		}
	)


def password_reset_request(request):
	message = []
	password_reset_form = UserPasswordResetForm()
	if request.method == "POST":
		try:
			password_reset_form = UserPasswordResetForm(request.POST)
			if password_reset_form.is_valid():
				data = password_reset_form.cleaned_data["email"]
				associated_users = User.objects.filter(email=data)
				if associated_users.exists():
					for user in associated_users:
						subject = "Восстановление пароля"
						uid = urlsafe_base64_encode(force_bytes(user.pk))
						token = default_token_generator.make_token(user)
						letter = f"Здравствуйте\nДля восстановления пароля на сайте {NAME}" \
								 f"перейдите по ссылке: https://{DOMAIN}/reset/{uid}/{token}"
						send_mail(
							receiver=data,
							subject=subject,
							message=letter
						)
						return redirect("/password_reset/done/")
		except Exception as e:
			logging.error(f"{type(e).__name__}: {str(e)}")
			message = ["False", f"{type(e).__name__}: {str(e)}"]
	return render(
		request,
		template_name="account/password_reset.html",
		context={
			"password_reset_form": password_reset_form,
			"message": message
		}
	)


def settings_view(request):
	if not request.user.is_authenticated:
		return redirect("/")
	if not request.user.profile.is_confirmed:
		return redirect("/confirm")
	profile = Profile.objects.filter(user=request.user).first()
	if not profile:
		html = "Ошибка: Профиль не создан"
		return HttpResponse(html)
	form_edit_full_name = EditFullName()
	full_name = profile.full_name
	dormitory = profile.dormitory
	categories = profile.categories.all()
	is_avatar = profile.is_avatar
	if request.method == "POST":
		if is_ajax(request):
			try:
				if request.POST.get("new_name"):
					profile.full_name = request.POST.get("new_name")
					profile.save()
					return JsonResponse(
						{
							"status": "success",
							"message": "Имя успешно изменено!"
						}
					)

				elif request.FILES.get("photo"):
					photo = request.FILES.get("photo")

					write_photo(photo=photo, base_name=request.user.username)

					if not is_avatar:
						profile.is_avatar = True
						profile.save()

					return JsonResponse(
						{
							"status": "success",
							"message": "Фото успешно загружено<br>Перезагрузка..."
						}
					)

			except Exception as e:
				logging.error(f"{type(e).__name__}: {str(e)}")
				return JsonResponse(
					{
						"status": "failed",
						"message": str(e.message) if str(
							type(e).__name__) == "ValidationError" else f"{type(e).__name__}: {str(e)}",
					}
				)

	return render(
		request,
		"account/settings.html",
		{
			"full_name": full_name,
			"dormitory": dormitory,
			"form_edit_full_name": form_edit_full_name,
			"categories": categories,
			"is_avatar": is_avatar,
		}
	)


def new_ad_view(request):
	if not request.user.is_authenticated:
		return redirect("/")
	if not request.user.profile.is_confirmed:
		return redirect("/confirm")
	message = []
	form = NewAd()
	try:
		if request.method == "POST":
			form = NewAd(request.POST)
			if form.is_valid():
				generated_id = generate_id()
				Advertisement.objects.create(
					identity=generated_id,
					title=form.cleaned_data["title"],
					description=form.cleaned_data["description"],
					category=form.cleaned_data["category"],
					price=form.cleaned_data["price"],
					seller=request.user, ).save()
				return redirect(f"/ad/{generated_id}")
	except Exception as e:
		logging.error(f"{type(e).__name__}: {str(e)}")
		message = ["False", f"{type(e).__name__}: {str(e)}"]

	return render(
		request,
		"ad/new_ad.html",
		{
			"form": form,
			"message": message,
		})


def ad_view(request, ad_pk):
	ad = Advertisement.objects.filter(identity=ad_pk).first()
	if not ad:
		raise Http404
	if request.method == "POST":
		if is_ajax(request):
			try:
				if request.POST.get("action"):
					request_action = request.POST.get("action")

					if request_action == "start_dialog":
						if ad.seller == request.user:
							return JsonResponse(
								{
									"status": "failed",
									"message": "Продавец является текущим пользователем"
								}
							)
						users = (request.user, ad.seller)
						dialog = Dialog.objects.filter(Q(user1__in=users) & Q(user2__in=users)).first()
						if not dialog:
							dialog = Dialog.objects.create(user1=request.user, user2=ad.seller)
							dialog.save()

						return JsonResponse(
							{
								"status": "success",
								"message": dialog.pk
							}
						)

					if not ((request.user == ad.seller) or request.user.is_staff):
						return JsonResponse(
							{
								"status": "failed",
								"message": "Not owner"
							}
						)

					if request_action == "activate":
						if not ad.is_moderated:
							return JsonResponse(
								{
									"status": "failed",
									"message": "Не прошло модерацию"
								}
							)
						if ad.is_photo_sent:
							ad.is_visible = True
							ad.save()
							return JsonResponse(
								{
									"status": "success"
								}
							)
						else:
							return JsonResponse(
								{
									"status": "failed",
									"message": "Сначала загрузите фото"
								}
							)

					elif request_action == "hide":
						if not ad.is_moderated:
							return JsonResponse(
								{
									"status": "failed",
									"message": "Не прошло модерацию"
								}
							)
						ad.is_visible = False
						ad.save()
						return JsonResponse(
							{
								"status": "success"
							}
						)

					elif request_action == "edit":
						return JsonResponse(
							{
								"status": "success"
							}
						)

					elif request_action == "delete":
						delete_photo(directory=f"{BASE_DIR}/static/img/", prefix=ad_pk)
						ad.delete()
						return JsonResponse(
							{
								"status": "success",
								"message": "Успешно удалено<br>Редирект..."
							}
						)

				elif request.FILES.getlist("photos[]"):
					if not ((request.user == ad.seller) or request.user.is_staff):
						return JsonResponse(
							{
								"status": "failed",
								"message": "Not owner"
							}
						)

					photos = request.FILES.getlist("photos[]")
					if len(photos) > 5:
						raise ValidationError("Ошибка: Вы можете выбрать не более 5 файлов")
					for i, photo in enumerate(photos):
						write_photo(photo=photo, base_name=ad_pk, extra_name=f"_{i}")

					ad.is_photo_sent = True
					ad.num_photos = len(photos)
					ad.save()

					return JsonResponse(
						{
							"status": "success",
							"message": "Фото успешно загружено.<br>Перезагрузка..."
						}
					)
			except Exception as e:
				logging.error(f"{type(e).__name__}: {str(e)}")
				return JsonResponse(
					{
						"status": "failed",
						"message": str(e.message) if str(
							type(e).__name__) == "ValidationError" else f"{type(e).__name__}: {str(e)}",
					}
				)

	message = []
	is_owner = True if ad.seller == request.user else False
	is_photo_sent = True if ad.is_photo_sent else False
	is_visible = True if ad.is_visible else False
	is_moderated = True if ad.is_moderated else False
	title = ad.title
	description = ad.description
	price = ad.price
	category = ad.category
	seller = ad.seller
	# TODO: переписать, неэффективно
	reviews = Review.objects.filter(user=ad.seller).all()
	rating = reviews.aggregate(avg_rating=Avg("mark"))["avg_rating"]
	if rating is None:
		rating = 0.0
	num_photos = 0

	try:
		if is_photo_sent:
			num_photos = [i for i in range(ad.num_photos)]
	except Exception as e:
		logging.error(f"{type(e).__name__}: {str(e)}")
		message = ["False", f"{type(e).__name__}: {str(e)}"]

	return render(
		request,
		"ad/ad.html",
		{
			"is_visible": is_visible,
			"is_owner": is_owner,
			"is_photo_sent": is_photo_sent,
			"is_moderated": is_moderated,
			"id": ad_pk,
			"title": title,
			"price": price,
			"description": description,
			"category": category,
			"seller": seller,
			"rating": rating,
			"num_photos": num_photos,
			"author": seller.username,
			"message": message,
		})


def edit_ad_view(request, ad_pk):
	if not request.user.is_authenticated:
		return redirect("/")
	if not request.user.profile.is_confirmed:
		return redirect("/confirm")
	ad = Advertisement.objects.filter(identity=ad_pk).first()
	if not ad:
		raise Http404
	if ad.seller != request.user:
		raise Http404

	message = []
	form = EditAd()
	if request.method == "POST":
		if is_ajax(request):
			try:
				if request.FILES.getlist("photos[]"):
					photos = request.FILES.getlist("photos[]")
					if len(photos) > 5:
						raise ValidationError("Ошибка: Вы можете выбрать не более 5 файлов")

					delete_photo(directory=f"{BASE_DIR}/static/img/", prefix=ad_pk)
					for i, photo in enumerate(photos):
						write_photo(photo=photo, base_name=ad_pk, extra_name=f"_{i}")

					ad.is_photo_sent = True
					ad.num_photos = len(photos)
					ad.save()

					return JsonResponse(
						{
							"status": "success",
							"message": "Фото успешно загружено.<br>Перезагрузка..."
						}
					)
			except Exception as e:
				logging.error(f"{type(e).__name__}: {str(e)}")
				return JsonResponse(
					{
						"status": "failed",
						"message": str(e.message) if str(
							type(e).__name__) == "ValidationError" else f"{type(e).__name__}: {str(e)}",
					}
				)
		else:
			try:
				form = EditAd(request.POST)
				if form.is_valid():
					if form.cleaned_data["title"]:
						ad.title = form.cleaned_data["title"]
					if form.cleaned_data["description"]:
						ad.description = form.cleaned_data["description"]
					if form.cleaned_data["price"]:
						ad.price = form.cleaned_data["price"]
					if form.cleaned_data["category"]:
						ad.category = form.cleaned_data["category"]

					ad.save()
					return redirect(f"/ad/{ad_pk}")

			except Exception as e:
				logging.error(f"{type(e).__name__}: {str(e)}")
				message = ["False", f"{type(e).__name__}: {str(e)}"]

	return render(
		request,
		"ad/edit_ad.html",
		{
			"id": ad_pk,
			"form": form,
			"message": message,
		})


def new_review_view(request, profile_pk):
	user = User.objects.filter(username=profile_pk).first()
	if not user:
		raise Http404
	if not request.user.is_authenticated:
		return redirect("/")
	if not request.user.profile.is_confirmed:
		return redirect("/confirm")
	if (timezone.now() - request.user.date_joined).days < 1:
		return HttpResponse("<h3>Вы не можете оставлять отзывы в течение суток</h3>")

	message = []
	form = NewReview()
	try:
		if request.method == "POST":
			form = NewReview(request.POST)
			if form.is_valid():
				generated_id = generate_id()
				Review.objects.create(
					identity=generated_id,
					user=user,
					mark=form.cleaned_data["mark"],
					text=form.cleaned_data["text"],
					reviewer=request.user,
				).save()

				return redirect(f"/profile/{profile_pk}/review/{generated_id}")
	except Exception as e:
		logging.error(f"{type(e).__name__}: {str(e)}")
		message = ["False", f"{type(e).__name__}: {str(e)}"]

	return render(
		request,
		"review/new_review.html",
		{
			"form": form,
			"message": message,
		})


def review_view(request, profile_pk, review_pk):
	review = Review.objects.filter(identity=review_pk).first()
	if not review:
		raise Http404
	user = User.objects.filter(username=profile_pk).first()
	if not user:
		raise Http404
	if request.method == "POST":
		if is_ajax(request):
			try:
				if request.POST.get("action"):
					request_action = request.POST.get("action")

					if request_action == "edit":
						return JsonResponse(
							{
								"status": "success"
							}
						)

					elif request_action == "delete":
						delete_photo(directory=f"{BASE_DIR}/static/img/", prefix=review_pk)
						review.delete()
						return JsonResponse(
							{
								"status": "success",
								"message": "Успешно удалено<br>Редирект..."
							}
						)

				elif request.FILES.getlist("photos[]"):
					photos = request.FILES.getlist("photos[]")
					if len(photos) > 5:
						raise ValidationError("Ошибка: Вы можете выбрать не более 5 файлов")
					for i, photo in enumerate(photos):
						write_photo(photo=photo, base_name=review_pk, extra_name=f"_{i}")

					review.is_photo_sent = True
					review.num_photos = len(photos)
					review.save()

					return JsonResponse(
						{
							"status": "success",
							"message": "Фото успешно загружено.<br>Перезагрузка..."
						}
					)
			except Exception as e:
				logging.error(f"{type(e).__name__}: {str(e)}")
				return JsonResponse(
					{
						"status": "failed",
						"message": str(e.message) if str(
							type(e).__name__) == "ValidationError" else f"{type(e).__name__}: {str(e)}",
					}
				)

	message = []
	is_owner = True if review.reviewer == request.user else False
	is_photo_sent = True if review.is_photo_sent else False
	text = review.text
	mark = review.mark
	updated_at = review.updated_at
	reviewer = review.reviewer
	num_photos = 0

	try:
		if is_photo_sent:
			num_photos = [i for i in range(review.num_photos)]
	except Exception as e:
		logging.error(f"{type(e).__name__}: {str(e)}")
		message = ["False", f"{type(e).__name__}: {str(e)}"]

	return render(
		request,
		"review/review.html",
		{
			"is_owner": is_owner,
			"is_photo_sent": is_photo_sent,
			"review_id": review_pk,
			"mark": mark,
			"text": text,
			"updated_at": updated_at,
			"user": user.username,
			"num_photos": num_photos,
			"author": reviewer.username,
			"message": message,
		})


def edit_review_view(request, profile_pk, review_pk):
	if not request.user.is_authenticated:
		return redirect("/")
	if not request.user.profile.is_confirmed:
		return redirect("/confirm")
	review = Review.objects.filter(identity=review_pk).first()
	if not review:
		raise Http404
	if review.reviewer != request.user:
		raise Http404

	message = []
	form = EditReview()
	if request.method == "POST":
		if is_ajax(request):
			try:
				if request.FILES.getlist("photos[]"):
					photos = request.FILES.getlist("photos[]")
					if len(photos) > 5:
						raise ValidationError("Ошибка: Вы можете выбрать не более 5 файлов")

					delete_photo(directory=f"{BASE_DIR}/static/img/", prefix=review_pk)
					for i, photo in enumerate(photos):
						write_photo(photo=photo, base_name=review_pk, extra_name=f"_{i}")

					review.is_photo_sent = True
					review.num_photos = len(photos)
					review.save()

					return JsonResponse(
						{
							"status": "success",
							"message": "Фото успешно загружено.<br>Перезагрузка..."
						}
					)
			except Exception as e:
				logging.error(f"{type(e).__name__}: {str(e)}")
				return JsonResponse(
					{
						"status": "failed",
						"message": str(e.message) if str(
							type(e).__name__) == "ValidationError" else f"{type(e).__name__}: {str(e)}",
					}
				)
		else:
			try:
				form = EditReview(request.POST)
				if form.is_valid():
					if form.cleaned_data["mark"]:
						review.mark = form.cleaned_data["mark"]
					if form.cleaned_data["text"]:
						review.text = form.cleaned_data["text"]

					review.save()
					return redirect(f"/profile/{review.user.username}/review/{review_pk}")

			except Exception as e:
				logging.error(f"{type(e).__name__}: {str(e)}")
				message = ["False", f"{type(e).__name__}: {str(e)}"]

	return render(
		request,
		"review/edit_review.html",
		{
			"review_id": review_pk,
			"profile_id": profile_pk,
			"form": form,
			"message": message,
		})


def edit_category_view(request):
	if not request.user.is_authenticated:
		return redirect("/")
	if not request.user.profile.is_confirmed:
		return redirect("/confirm")
	profile = Profile.objects.filter(user=request.user).first()
	message = []
	form = EditCategory()
	if request.method == "POST":
		try:
			form = EditCategory(request.POST)
			if form.is_valid():
				if form.cleaned_data["categories"]:
					profile.categories.set(form.cleaned_data["categories"])

				profile.save()
				return redirect(f"/account/settings/")

		except Exception as e:
			logging.error(f"{type(e).__name__}: {str(e)}")
			message = ["False", f"{type(e).__name__}: {str(e)}"]

	return render(
		request,
		"account/edit_category.html",
		{
			"form": form,
			"message": message,
		})


def dialogs_view(request):
	if not request.user.is_authenticated:
		return redirect("/")
	if not request.user.profile.is_confirmed:
		return redirect("/confirm")

	dialogs = Dialog.objects.filter(Q(user1=request.user) | Q(user2=request.user))
	dialogs = [
		{
			"pk": dialog.pk,
			"user": dialog.user1 if dialog.user1 != request.user else dialog.user2,
			"last_msg": Message.objects.filter(dialog=dialog).last()
		}
		for dialog in dialogs
	]

	return render(
		request,
		"dialog/dialogs.html",
		{
			"dialogs": dialogs,
		}
	)


def dialog_view(request, dialog_pk):
	if not request.user.is_authenticated:
		return redirect("/")
	if not request.user.profile.is_confirmed:
		return redirect("/confirm")

	dialog = Dialog.objects.filter(pk=dialog_pk).first()
	if not dialog:
		raise Http404
	if request.user not in (dialog.user1, dialog.user2):
		raise Http404

	partner = dialog.user1 if request.user != dialog.user1 else dialog.user2
	if request.method == "POST":
		if is_ajax(request):
			message = request.POST.get("message")

			new_message = Message(
				dialog=dialog,
				sender=request.user,
				message=message,

			).save()

	messages = dialog.get_messages()

	return render(
		request,
		"dialog/dialog.html",
		{
			"messages": messages,
			"partner": partner
		}
	)


def moderate_view(request):
	if not request.user.is_staff:
		raise Http404
	if request.method == "POST":
		if is_ajax(request):
			try:
				if request.POST.get("action"):
					request_action = request.POST.get("action").split("-")

					if request_action[0] == "allow":
						ad = Advertisement.objects.filter(identity=request_action[1]).first()
						if ad:
							ad.is_moderated = True
							ad.save()
							subject = "Объявление одобрено"
							msg = f"Здравствуйте, {ad.seller}\nВаше объявление '{ad.title}' одобрено. Теперь вы можете нажать 'Показать' на странице с объявлением и оно будет доступно всем."
							send_mail(
								subject=subject,
								message=msg,
								receiver=ad.seller.profile.email
							)
						return JsonResponse(
							{
								"status": "success"
							}
						)

					elif request_action[0] == "deny":
						ad = Advertisement.objects.filter(identity=request_action[1]).first()
						if ad:
							ad.delete()
							subject = "Объявление удалено"
							msg = f"Здравствуйте, {ad.seller}\nВаше объявление '{ad.title}' не прошло модерацию и оно было удалено."
							send_mail(
								subject=subject,
								message=msg,
								receiver=ad.seller.profile.email
							)
						return JsonResponse(
							{
								"status": "success"
							}
						)

			except Exception as e:
				logging.error(f"{type(e).__name__}: {str(e)}")
				return JsonResponse(
					{
						"status": "failed",
						"message": str(e.message) if str(
							type(e).__name__) == "ValidationError" else f"{type(e).__name__}: {str(e)}",
					}
				)
	ads = []
	try:
		ads = Advertisement.objects.filter(is_moderated=False).all()
	except Exception as e:
		logging.error(f"{type(e).__name__}: {str(e)}")

	return render(
		request,
		"account/moderate.html",
		{
			"ads": ads,
		}
	)


def edit_dormitory_view(request):
	if not request.user.is_authenticated:
		return redirect("/")
	if not request.user.profile.is_confirmed:
		return redirect("/confirm")
	profile = Profile.objects.filter(user=request.user).first()
	message = []
	form = EditDormitory()
	if request.method == "POST":
		try:
			form = EditDormitory(request.POST)
			if form.is_valid():
				profile.dormitory = form.cleaned_data["dormitory"]
				profile.save()

				return redirect(f"/account/settings/")

		except Exception as e:
			logging.error(f"{type(e).__name__}: {str(e)}")
			message = ["False", f"{type(e).__name__}: {str(e)}"]

	return render(
		request,
		"account/edit_dormitory.html",
		{
			"form": form,
			"message": message,
		})
