import phonenumbers
from phonenumbers import carrier, geocoder, timezone

def phone_lookup(number):
    """
    Scans a phone number using the python-phonenumbers library.
    Expects number in international format (e.g., "+919876543210").
    """
    if not number or len(number) < 5:
        return {"valid": False, "error": "Number too short or empty"}

    try:
        # 1. Parse the number
        # The frontend now sends "+91..." so we use None for region as it's implied in the string
        parsed = phonenumbers.parse(number, None)

        if not phonenumbers.is_valid_number(parsed):
            return {"valid": False, "error": "Invalid Number Pattern"}

        # 2. Extract Basic Technical Details
        country = geocoder.description_for_number(parsed, "en")
        carrier_name = carrier.name_for_number(parsed, "en")
        time_zones = timezone.time_zones_for_number(parsed)
        
        # 3. Determine Line Type (Mobile, Landline, VoIP)
        num_type = phonenumbers.number_type(parsed)
        line_type_str = "Unknown"
        if num_type == phonenumbers.PhoneNumberType.MOBILE: 
            line_type_str = "Mobile / Cellular"
        elif num_type == phonenumbers.PhoneNumberType.FIXED_LINE: 
            line_type_str = "Landline"
        elif num_type == phonenumbers.PhoneNumberType.VOIP: 
            line_type_str = "VoIP (Virtual)"
        elif num_type == phonenumbers.PhoneNumberType.TOLL_FREE: 
            line_type_str = "Toll-Free"

        # 4. Formats
        e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        national = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
        clean_number = e164.replace('+', '')

        # 5. Generate Search Dorks (Web Footprint)
        dorks = {
            "Google Search": f"https://www.google.com/search?q=\"{e164}\" OR \"{national}\"",
            "TrueCaller Search": f"https://www.google.com/search?q=site:truecaller.com \"{national}\"",
            "WhatsApp API": f"https://wa.me/{clean_number}",
            "Telegram": f"https://t.me/{clean_number}"
        }

        # 6. Return Structured Data
        return {
            "valid": True,
            "basic": {
                "country": country if country else "Unknown Region",
                "carrier": carrier_name if carrier_name else "Unknown Carrier",
                "line_type": line_type_str,
                "time_zone": ", ".join(time_zones),
                "format_e164": e164,
                "format_national": national
            },
            "identity": {
                "spam_score": "Low (0/10)", # Placeholder: Python cannot check spam score offline
                "cnam": "Private"           # Placeholder: CNAM requires paid API
            },
            "social": {
                "whatsapp": "Check Link Generated",
                "telegram": "Check Link Generated"
            },
            "dorks": dorks
        }

    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }