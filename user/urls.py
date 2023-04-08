from django.urls import path
from user.views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('', index, name="homepage"),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/api/signin/', SignInView.as_view(), name='SignIn'),
    path('user/api/signup/', UserSignupView.as_view(), name='user-signup'),
    path('user/api/details/', UserDetailAPI.as_view(), name='SignIn'),
    path('user/api/change_password/', ChangePasswordView.as_view(), name='ChangePassword'),
    path('user/api/forgot_password/', ForgotPasswordView.as_view(), name='ForgotPassword'),
]
