import logging
import os
import random
from typing import Any

from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest

from apps.backend import backend

logging.basicConfig(
	level=logging.INFO,
	filename="backend_views.log",
	filemode="a+",
	format="%(asctime)s %(levelname)s %(message)s"
)


def generate_code() -> int:
	return random.randint(100000, 999999)


def generate_id() -> str:
	alphabet = "abcdefghijklmnopqrstuvwxyz1234567890"
	gen_id = ""

	for i in range(32):
		gen_id += random.choice(alphabet)

	return gen_id


def send_mail(receiver: str, subject: str, message: str) -> bool:
	try:
		backend.Email(_receiver=receiver, _subject=subject, _message=message).send_email()
		logging.info(f"[+] (send mail) Email sent to {receiver}")
		return True
	except Exception as e:
		logging.error(f"[-] (send mail) error: {type(e).__name__}: {str(e)}")
		raise ValidationError(f"[-] (send mail) error: {type(e).__name__}: {str(e)}")


def is_ajax(request: WSGIRequest) -> bool:
	return request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"


def write_photo(photo: Any, base_name: str, extra_name: str = "") -> bool:
	if photo.name[-3:] != "jpg":
		raise ValidationError("Ошибка: Расширение должно быть JPG")

	with open("static/img/" + f"{base_name}{extra_name}.{photo.name[-3:]}", "wb+") as destination:
		for chunk in photo.chunks():
			destination.write(chunk)
	return True


def delete_photo(directory: str, prefix: str):
	for item in os.listdir(directory):
		path = os.path.join(directory, item)
		if item.startswith(prefix):
			if os.path.isfile(path):
				os.remove(path)
