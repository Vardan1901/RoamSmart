from django import forms
from .models import Trip, Expense
from decimal import Decimal

class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ("destination", "start_date", "end_date", "budget")
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "budget": forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }


class ExpenseForm(forms.ModelForm):
    # Add a custom field for INR amount
    amount_inr = forms.DecimalField(
        label='Amount (₹)',
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Enter amount in ₹'
        })
    )

    class Meta:
        model = Expense
        fields = ("name", "amount_inr", "date", "category", "description")
        widgets = {
            "name": forms.TextInput(attrs={'class': 'form-control'}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "category": forms.Select(attrs={'class': 'form-control'}),
            "description": forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing an existing expense, convert USD amount to INR
        if self.instance and self.instance.pk:
            self.initial['amount_inr'] = self.instance.amount * Decimal('83')
        # Remove the original amount field as we're using amount_inr instead
        if 'amount' in self.fields:
            del self.fields['amount']

    def save(self, commit=True):
        expense = super().save(commit=False)
        # Convert INR amount back to USD before saving
        amount_inr = self.cleaned_data['amount_inr']
        expense.amount = amount_inr / Decimal('83')
        if commit:
            expense.save()
        return expense 