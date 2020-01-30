from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.http import Http404
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model

from ..backend.account import account_bookmarks, account_positions
from ..forms import SignUpForm, EditAccountForm
from ..models import User
User = get_user_model()


class AccountView(TemplateView):
    model = User
    template_name = 'account/account.html'

    def dispatch(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect('login')

        return super(AccountView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AccountView, self).get_context_data(**kwargs)
        request = self.request

        user = request.user

        if request.user.is_authenticated:

            account_bookmarks.get_user_favourites(user, context)
            account_positions.get_open_positions(user, context)
            account_positions.get_closed_positions(user, context)

            for fav in context['favourites'].iterator():
                account_bookmarks.check_is_favourite(user, fav, context)

            return context

        else:
            messages.success(request, "Please log in")
            return context


def signup(request):
    if not request.user.is_authenticated:
        if request.method == 'POST':
            form = SignUpForm(request.POST)

            if form.is_valid():
                user = form.save(commit=False)
                user.is_active = True
                user.save()

                login(request, user)
                messages.success(request, "Success, you now have an account")

                return redirect('index')

            else:
                for msg in form.error_messages:
                    messages.error(request, f"{msg}: {form.error_messages[msg]}")

                    return render(request,
                                  "account/signup.html",
                                  {"form": form})

        else:
            form = SignUpForm()
        return render(request, 'account/signup.html', {'form': form})

    else:
        messages.info(request, 'You are logged in as: {}'.format(request.user.email))
        return redirect('index')


def login_request(request):

    if request.method == 'POST':
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            print(email, password)
            user = authenticate(email=email, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {email}")
                return redirect('/')
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Invalid email or password.")
    form = AuthenticationForm()
    return render(request,
                  'account/login.html',
                  {'form': form})


def logout_request(request):
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, 'Logged Out')

        return redirect('index')
    else:
        return redirect('index')


def edit_account(request):
    if request.user.is_authenticated:

        if request.method == 'POST':
            form = EditAccountForm(request.POST, instance=request.user)

            if form.is_valid():
                prev_currency = request.user.base_currency
                user = form.save(commit=False)
                user.change_currency(prev_currency)
                user.get_account_value()

                return redirect('/account')

        else:
            form = EditAccountForm(instance=request.user)
            args = {'form': form}
            return render(request,
                          'account/edit_account.html',
                          args)
    else:
        return redirect('login')


def change_password(request):
    if request.user.is_authenticated:

        if request.method == 'POST':
            form = PasswordChangeForm(data=request.POST, user=request.user)

            if form.is_valid():
                form.save()
                update_session_auth_hash(request, form.user)
                return redirect('/account')
            else:
                return redirect('/account/change_password')

        else:
            form = PasswordChangeForm(user=request.user)
            args = {'form': form}
            return render(request,
                          'account/change_password.html',
                          args)
    else:
        return redirect('login')


def verify(request, uuid):
    try:
        user = User.objects.get(verification_uuid=uuid, is_verified=False)
    except User.DoesNotExist:
        raise Http404("User does not exist or is already verified")

    user.is_verified = True
    user.save()

    return redirect('index')
