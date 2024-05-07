from django.contrib.auth.views import PasswordResetDoneView, PasswordResetConfirmView, \
    PasswordResetCompleteView, LogoutView
from django.urls import path
from apps.frontend.views import index_view, login_view, register_view, account_view, confirm_view, \
    password_reset_request, settings_view, new_ad_view, ad_view, edit_ad_view, other_account_view, new_review_view, \
    review_view, edit_review_view, edit_category_view, dialogs_view, dialog_view

urlpatterns = [
    path("", index_view, name="index"),
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("logout/", LogoutView.as_view(next_page="/"), name="logout"),
    path("account/", account_view, name="account"),
    path("account/settings/", settings_view, name="settings"),
    path("account/new_ad/", new_ad_view, name="new_ad"),
    path("account/edit_category/", edit_category_view, name="edit_category"),
    path("account/dialogs/", dialogs_view, name="dialogs"),
    path("account/dialogs/<str:dialog_pk>", dialog_view, name="dialog"),
    path("profile/<str:profile_pk>/", other_account_view, name="other_account"),
    path("ad/<str:ad_pk>/", ad_view, name="ad_page"),
    path("ad/<str:ad_pk>/edit/", edit_ad_view, name="edit_ad"),
    path("profile/<str:profile_pk>/new_review/", new_review_view, name="new_review"),
    path("profile/<str:profile_pk>/review/<str:review_pk>/", review_view, name="review_page"),
    path("profile/<str:profile_pk>/review/<str:review_pk>/edit/", edit_review_view, name="edit_review"),
    path("confirm/", confirm_view, name="confirm"),
    path("password_reset/", password_reset_request, name="password_reset"),
    path("password_reset/done/", PasswordResetDoneView.as_view(template_name="account/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", PasswordResetConfirmView.as_view(template_name="account/password_reset_confirm.html"), name="password_reset_confirm"),
    path("reset/done/", PasswordResetCompleteView.as_view(template_name="account/password_reset_complete.html"), name="password_reset_complete"),
]
