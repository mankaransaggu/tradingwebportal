from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.contrib.auth.models import User
from . import models


class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.', required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    #
    # def save(self, commit=True):
    #     user = super(SignUpForm, self).save(commit=False)
    #     user


class EditAccountForm(UserChangeForm):

    class Meta:
        model = User
        fields = (
            'email',
            'first_name',
            'last_name',
            'password',
            )


class CreatePositionForm(forms.ModelForm):

    class Meta:
        model = models.Position
        fields = ('open_date',
                  'direction',
                  'quantity',
                  'open_price',
                  'stock')

