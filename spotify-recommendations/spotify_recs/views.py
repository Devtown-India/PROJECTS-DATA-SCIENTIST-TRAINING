from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from spotify_recs import settings
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.contrib.auth import logout


class HomePage(TemplateView):
    template_name = "index.html"
