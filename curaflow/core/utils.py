from datetime import date


def calculate_age(birth_date):
    today = date.today()
    # Subtract birth year from current year
    age = today.year - birth_date.year
    # Adjust by subtracting 1 if today's (month, day) is before birth (month, day)
    # Python treats True as 1 and False as 0 in this subtraction
    age -= (today.month, today.day) < (birth_date.month, birth_date.day)
    return age