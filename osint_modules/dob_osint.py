import re

def check_dob_exposure(text_data, dob):
    pattern = dob.replace("-", "[/-]")
    for text in text_data:
        if re.search(pattern, text):
            return True
    return False
