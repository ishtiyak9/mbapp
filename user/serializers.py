from rest_framework import serializers
from user.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.password_validation import validate_password


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "fullname", "email", "is_active", "password"]

    def validate_email(self, value):
        """
        Validate that the email field is in the correct format.
        """
        try:
            validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Email field is not in the correct format.")
        return value

    def validate_password(self, value):
        """
        Validate that the password field meets Django's password requirements.
        """
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate_fullname(self, value):
        """
        Validate that the fullname field is not empty.
        """
        if not value:
            raise serializers.ValidationError("Full Name field is required.")
        return value

    def create(self, validated_data):
        """
        Create and return a new User instance, given the validated data.
        """
        user = User.objects.create_user(**validated_data)
        return user
