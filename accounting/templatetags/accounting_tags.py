from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Gets an item from a dictionary by key.
    Usage: {{ my_dict|get_item:my_key }}
    """
    if dictionary and key:
        return dictionary.get(key)
    return None


@register.filter
def currency(value):
    """
    Formats a value as currency.
    Usage: {{ value|currency }}
    """
    try:
        return "{:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return "0.00"
