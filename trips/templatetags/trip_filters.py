from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def inr(value):
    """Format value as Indian Rupees"""
    try:
        value = Decimal(str(value))
        return f"₹{value:,.2f}"
    except (ValueError, TypeError):
        return value 