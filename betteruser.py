from django.db import models, transaction, IntegrityError
from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.backends import ModelBackend

import enum, re

# Custom user model and login backends

class LoginException(Exception):
	"""Abstract base class for the reasons a login fails."""
	pass
class InactiveAccount(LoginException):
	# is_active==False
	def __str__(self):
		return "The account is disabled."
class InvalidCredentials(LoginException):
	def __str__(self):
		return "The email address is not valid. Please check for typos."
class IncorrectCredentials(LoginException):
	def __str__(self):
		return "The email address and password did not match an account here."

class UserManager(models.Manager):
	# used by django.contrib.auth.backends.ModelBackend
	def get_by_natural_key(self, key):
		return User.objects.get(email=key)

	# support the createsuperuser management command.
	def create_superuser(self, email, password, **extra_fields):
		user = User(email=email)
		user.is_staff = True
		user.is_superuser = True
		user.set_password(password)
		user.save()
		return user

class User(AbstractBaseUser, PermissionsMixin):
	"""Our user model, where the primary identifier is an email address."""
	# https://github.com/django/django/blob/master/django/contrib/auth/models.py#L395
	email = models.EmailField(unique=True)
	is_staff = models.BooleanField(default=False, help_text='Whether the user can log into this admin.')
	is_active = models.BooleanField(default=True, help_text='Unselect this instead of deleting accounts.')
	date_joined = models.DateTimeField(default=timezone.now)

	# custom user model requirements
	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = []
	def get_full_name(self): return self.email
	def get_short_name(self): return self.email
	class Meta:
		verbose_name = 'user'
		verbose_name_plural = 'users'
	objects = UserManager()

	@staticmethod
	def get_or_create(email):
		# Get or create a new User for the email address. The User table
		# is not locked, so handle concurrency optimistically. The rest is
		# based on Django's default create_user.
		try:
			# Does the user exist?
			return User.objects.get(email=email)
		except User.DoesNotExist:
			try:
				# In order to recover from an IntegrityError
				# we must wrap the error-prone part in a
				# transaction. Otherwise we can't execute
				# further queries from the except block.
				# Not sure why. Occurs w/ Sqlite.
				with transaction.atomic():
					# Try to create it.
					user = User(email=email)
					user.set_unusable_password()
					user.save()
					return user
			except IntegrityError:
				# Creation failed (unique key violation on username),
				# so try to get it again. If this fails, something
				# weird happened --- just raise an exception then.
				return User.objects.get(email=email)

	@staticmethod
	def authenticate(email, password):
		# Returns an authenticated User object for the email and password,
		# or raises a LoginException on failure.
		user = authenticate(email=email, password=password)
		if user is not None:
			if not user.is_active:
				# Account is disabled.
				raise InactiveAccount()
			else:
				return user
		else:
			# Login failed. Why? If a user with that email exists,
			# return Incorrect.
			if User.objects.filter(email=email).exists():
				raise IncorrectCredentials()

			else:
				# If it's because the email address is itself invalid, clue the user to that.
				# But only do a simple regex check.
				if validate_email(email, simple=True) == ValidateEmailResult.Invalid:
					raise InvalidCredentials()
				else:
					# The email address is reasonable, but not in our system. Don't
					# reveal whether the email address is registered or not. Just
					# say the login is incorrect.
					raise IncorrectCredentials()


class DirectLoginBackend(ModelBackend):
	# Register in settings.py!
	# Django can't log a user in without their password. Before they create
	# a password, we use this to log them in. Registered in settings.py.
	supports_object_permissions = False
	supports_anonymous_user = False
	def authenticate(self, user_object=None):
		return user_object

# Validation

class ValidateEmailResult(enum.Enum):
	Invalid = 1
	Valid = 2
	Error = 3

def validate_email(email, simple=False):
	# First check that the email is of a valid form.

	# Based on RFC 2822 and https://github.com/SyrusAkbary/validate_email/blob/master/validate_email.py,
	# these characters are permitted in email addresses.
	ATEXT = r'[\w!#$%&\'\*\+\-/=\?\^`\{\|\}~]' # see 3.2.4

	# per RFC 2822 3.2.4
	DOT_ATOM_TEXT_LOCAL = ATEXT + r'+(?:\.' + ATEXT + r'+)*'
	DOT_ATOM_TEXT_HOST = ATEXT + r'+(?:\.' + ATEXT + r'+)+' # at least one '.'

	# per RFC 2822 3.4.1
	ADDR_SPEC = '^%s@(%s)$' % (DOT_ATOM_TEXT_LOCAL, DOT_ATOM_TEXT_HOST)

	m = re.match(ADDR_SPEC, email)
	if not m:
		return ValidateEmailResult.Invalid

	if simple:
		return ValidateEmailResult.Valid

	domain = m.group(1)
	
	# Check that the domain resolves to MX records, or the A/AAAA fallback.

	import dns.resolver
	resolver = dns.resolver.get_default_resolver()
	try:
		# Try resolving for MX records and get them in sorted priority order.
		response = dns.resolver.query(domain, "MX")
		mtas = sorted([(r.preference, str(r.exchange).rstrip('.')) for r in response])
	except (dns.resolver.NoNameservers, dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):

		# If there was no MX record, fall back to an A record.
		try:
			response = dns.resolver.query(domain, "A")
			mtas = [(0, str(r)) for r in response]
		except (dns.resolver.NoNameservers, dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):

			# If there was no A record, fall back to an AAAA record.
			try:
				response = dns.resolver.query(domain, "AAAA")
				mtas = [(0, str(r)) for r in response]
			except (dns.resolver.NoNameservers, dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
				# If there was any problem resolving the domain name,
				# then the address is not valid.
				return ValidateEmailResult.Invalid
	except Exception as e:
		# Some unhandled condition should not propagate.
		return ValidateEmailResult.Error

	return ValidateEmailResult.Valid

