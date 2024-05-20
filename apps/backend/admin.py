from django.contrib import admin

from apps.backend.models import Category, Profile, Review, Advertisement, Dialog, Message, Dormitory


@admin.register(Category)
@admin.register(Profile)
@admin.register(Review)
@admin.register(Advertisement)
@admin.register(Dialog)
@admin.register(Message)
@admin.register(Dormitory)
class ModelAdmin(admin.ModelAdmin):
	pass
