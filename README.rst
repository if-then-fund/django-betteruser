django-betteruser
=================

A better User model and helper functions for Django 1.7+.

* Email/password login (rather than username/password).
* Email address validation function that checks the form of the address and also that the domain part resolves.
* ``User.get_or_create(email)`` helper function handles concurrency better.
* ``User.authenticate(email, password)`` helper function takes care of the usual logic: call authenticate(); is the user active?
* Provides a DirectLoginBackend so that you can ``authenticate(user_object=user)`` user objects directly.

Installation
------------

* Copy ``betteruser.py`` into your app. It must be inside an app, and for simpliciy this project doesn't provide an app. You need to move it into your own app.
* In ``settings.py``, set ``AUTH_USER_MODEL`` to ``appname.betteruser.User``.
* Implement your concrete User class. In your own `models.py`, create a derived User class where you can add your own additional fields.

	from betteruser import User as UserBase, UserManagerBase

	class UserManager(UserManagerBase):
		def _get_user_class(self):
			return User

	class User(UserBase):
		objects = UserManager()
		# your additional model fields here, if any

Usage
-----

Creating a user::

	from email_validator import EmailNotValidError
	try:
		user = User.get_or_create(email)
	except EmailNotValidError:
		# Do stuff.
		# See https://github.com/JoshData/python-email-validator.

Logging a user in::

	from django.contrib.auth import login
	from yourapp.betteruser import InactiveAccount, InvalidCredentials, IncorrectCredentials

	def do_login(request):
		email = request.POST['email'].strip()
		password = request.POST['password'].strip()

		try:
			user = User.authenticate(email, password)
		except InactiveAccount:
			... # account is inactive
		except InvalidCredentials:
			... # email isn't a valid email address ("me@qqq")
		except IncorrectCredentials:
			... # email/password incorrect

		login(request, user)

DirectLoginBackend
------------------

To use the direct login backend, add to your settings.py::

	AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend', 'betteruser.DirectLoginBackend']

then call::

	user = User.objects.get_or_create(email="me@example.com")
	user = authenticate(user_object=user)

