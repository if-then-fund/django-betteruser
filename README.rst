django-betteruser
=================

A better User model and helper functions for Django 1.7+.

* Provides an abstract base User model that you can attach your own model fields too.
* The model is based around email/password login rather than username/password.
* Email address validation in ``User.get_or_create`` and ``User.authenticate`` checks the form of the address and also that the domain part resolves.
* ``User.get_or_create(email)`` handles concurrency better than Django's user creation helper method.
* ``User.authenticate(email, password)`` takes care of the usual logic when calling authenticate().
* Provides a DirectLoginBackend so that you can ``authenticate(user_object=user)`` user objects directly when you have authenticated a user yourself by other means.

Installation
------------

* Copy ``betteruser.py`` into your app. It must be inside an app, and for simpliciy this project doesn't provide an app. You need to move it into your own app.
* In ``settings.py``, set ``AUTH_USER_MODEL`` to ``appname.betteruser.User`` and set ``VALIDATE_EMAIL_DELIVERABILITY`` to ``True`` or ``False`` if you want email address validation to check that the domain part of addresses resolve (handy to turn off during unit testing to avoid network accesses).
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

