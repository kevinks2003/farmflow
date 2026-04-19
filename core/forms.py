from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User,Crop  # ✅ import custom user

class CustomUserCreationForm(UserCreationForm):
    phone = forms.CharField(
        max_length=10,
        required=True,
        help_text="Enter your 10-digit phone number"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role', 'phone', 'place', 'district']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap styling to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"

        # ✅ Force IDs for password fields (needed for toggle eye button)
        self.fields["password1"].widget.attrs["id"] = "password1"
        self.fields["password2"].widget.attrs["id"] = "password2"

    # Validation: username only alphabets
    def clean_username(self):
        username = self.cleaned_data.get("username", "")
        if not username.isalpha():
            raise forms.ValidationError("Username must contain only alphabets (A-Z).")
        return username

    # Validation: place only alphabets
    def clean_place(self):
        place = self.cleaned_data.get("place", "")
        if place and not place.isalpha():
            raise forms.ValidationError("Place must contain only alphabets (A-Z).")
        return place

    # Validation: district only alphabets
    def clean_district(self):
        district = self.cleaned_data.get("district", "")
        if district and not district.isalpha():
            raise forms.ValidationError("District must contain only alphabets (A-Z).")
        return district

    # Validation: email must end with @gmail.com
    def clean_email(self):
        email = self.cleaned_data.get("email", "")
        if not email.endswith("@gmail.com"):
            raise forms.ValidationError("Email must be a Gmail address (ending with @gmail.com).")
        return email

    # Validation: phone must be 10 digits only
    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        if not phone.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")
        if len(phone) != 10:
            raise forms.ValidationError("Phone number must be exactly 10 digits.")
        return phone


    
    
# ✅ New Crop Form
class CropForm(forms.ModelForm):
    class Meta:
        model = Crop
        fields = ["name", "quantity", "price", "image"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        
