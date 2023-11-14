from django.contrib.auth.backends import BaseBackend
from .models import User


class UserBackend(BaseBackend):
  def authenticate(self, request, uuid=None, email=None, password=None):
      # return super().authenticate(request, **kwargs)

      if email and password:
        try:
          user = User.objects.get(email=email)
        except User.DoesNotExist:
          return None
        else:
          if user.check_password(password):
            return user
          return None

      if uuid is None:
        return None

      try:
        user = User.objects.get(id=uuid)

      except User.DoesNotExist:
        user = User(username='user{}'.format(User.objects.count()+1))
        user.save()

      return user


  def get_user(self, user_id):
      # return super().get_user(user_id)

      try:
        return User.objects.get(pk=user_id)

      except User.DoesNotExist:
        return None
