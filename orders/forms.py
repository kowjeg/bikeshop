from django import forms

class CheckoutForm(forms.Form):
    PAYMENT_CHOICES = [
        ('debit', 'Debit Card'),
        ('wallet', 'Wallet Card'),
        ('cod', 'Cash On Delivery')
    ]
    full_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    city = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    payment_type = forms.CharField(widget=forms.Select(choices=PAYMENT_CHOICES))