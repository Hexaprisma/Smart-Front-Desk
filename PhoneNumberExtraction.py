import re
class PhoneNumberExtraction:
    def extract_phone_number(text):
        #Regular expression pattern for matching phone numbers
        phone_pattern = re.compile(r'\b\d{10}\b')

        match = phone_pattern.search(text)

        if match:
            return match.group()
        else:
            return None