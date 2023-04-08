from django.contrib.auth.hashers import check_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db.utils import IntegrityError
from django.shortcuts import render
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mbapp import settings
from user.models import User
from user.serializers import UserSerializer
from user.utils import get_tokens_for_user


def index(request):
    """
    Renders the index.html template.

    Parameters:
    request (HttpRequest): The HTTP request object.

    Returns:
    HttpResponse: The rendered response object containing the HTML of the index page.
    """
    return render(request, 'index.html', {})


class UserSignupView(CreateAPIView):
    """
    A view for handling user signup requests. Uses the UserSerializer to validate and create new users.

    POST parameters:
    - email: The email address for the new user.
    - password: The password for the new user.
    - first_name: The first name of the new user (optional).
    - last_name: The last name of the new user (optional).

    Returns:
    A JSON response containing the details of the new user, including an authentication token.

    Raises:
    400 Bad Request: If the request is invalid or the email address is already in use.
    """
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests for creating new users.

        Parameters:
        request (HttpRequest): The HTTP request object.

        Returns:
        HttpResponse: A JSON response containing the details of the new user.

        Raises:
        ValidationError: If the request data is invalid.
        IntegrityError: If the email address is already in use.
        """
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response({'errors': e.detail}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.save()
        except IntegrityError:
            return Response({'errors': {'email': 'Email already exists.'}}, status=status.HTTP_400_BAD_REQUEST)
        user = {
            "id": serializer.data['id'],
            "fullname": serializer.data['fullname'],
            "email": serializer.data['email'],
            "is_active": serializer.data['is_active'],
            "token": get_tokens_for_user(user),
        }
        return Response({'user': user}, status=status.HTTP_201_CREATED)


class SignInView(APIView):
    permission_classes = [AllowAny]
    """
        SignInView class let user login using email and password

        :param p1: email taken from authorization token.
        :param p2: password taken from raw json body request.
        :return: return datapack with access code and refresh code or send message of failed with status code
        """

    def post(self, request, *args, **kwargs):
        email = request.data['email']
        password = request.data['password']
        try:
            user = User.objects.get(email=email)
        except:
            response = {
                'success': False,
                'status_code': 404,
                'message': 'User with this email does not exist.'
            }
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        if not user.is_active:
            response = {
                'success': False,
                'status_code': 403,
                'message': 'Account is not active.'
            }
            return Response(response, status=status.HTTP_403_FORBIDDEN)

        if not check_password(password, user.password):
            response = {
                'success': False,
                'status_code': 401,
                'message': 'Email and password do not match.'
            }
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)

        # response data pack as return value
        response = {
            'success': True,
            'status_code': 200,
            'message': 'Tokens successfully generated.',
            'data': get_tokens_for_user(user)

        }
        return Response(response, status=status.HTTP_200_OK)


# Class based view to Get User Details using Token Authentication
class UserDetailAPI(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        """
        HTTP GET method to handle requests to retrieve user details.

        Args:
            request (HttpRequest): The HTTP request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: A Response object with the serialized user data and a 200 OK status code.
        """
        user = User.objects.get(id=request.user.id)
        serializer = UserSerializer(user)
        response = {
            'user_details': serializer.data
        }
        return Response(response, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    """
    ChangePasswordView class let user change/update their current password

    :param p1: user ID taken from authorization token.
    :param p2: current_password taken from raw json body request.
    :param p3: new_password taken from raw json body request.
    :param p4: confirm_password taken from raw json body request.
    :return: send message of success or failed with status code
    """

    def post(self, request, *args, **kwargs):
        user = request.user
        current_password = request.data['current_password']

        if not check_password(current_password, user.password):
            response = {
                'success': False,
                'status_code': 401,
                'message': 'Old password does not match.'
            }
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)

        new_password = request.data['new_password']
        confirm_password = request.data['confirm_password']

        if new_password != confirm_password:
            response = {
                'success': False,
                'status_code': 401,
                'message': 'Passwords do not match.'
            }
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)

        user.set_password(new_password)
        user.save()
        response = {
            'success': True,
            'status_code': 200,
            'message': 'Password changed successfully.'
        }
        return Response(response, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    """
        ForgotPasswordView class let user reset their password if they forget by taking email s input
        Handles password reset tokens When a token is created, an e-mail needs to be sent to the user
        :param p1: email taken from authorization token. 
        :return: If success is true then send a email with reset url to the user email else return a success == false message """

    def post(self, request, *args, **kwargs):
        email = request.data['email']

        try:
            user = User.objects.get(email=email)
        except:
            response = {
                'success': False,
                'status_code': 404,
                'message': 'User with this email does not exist.'
            }
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        uid_b64 = urlsafe_base64_encode(force_bytes(user.id))
        token = default_token_generator.make_token(user)

        # change to the host of the frontend client
        # after frontend deployment
        reset_password_link = 'https://inmeet-manager.com/reset_password?id=' + uid_b64 + '&token=' + token
        print('reset_password_link: ', reset_password_link)

        # send email
        send_mail(
            subject='InMeet password reset link',
            message='Please go to this link to reset your password: ' + reset_password_link,
            from_email=settings.EMAIL_SENDER,
            recipient_list=[email],
            fail_silently=False,
        )
        print('------------------Email Sent------------------')

        response = {
            'success': True,
            'status_code': 200,
            'message': 'Password reset link has been sent to your email.'
        }
        return Response(response, status=status.HTTP_200_OK)
