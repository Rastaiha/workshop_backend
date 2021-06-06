from rest_framework.exceptions import ValidationError

from workshop_backend.settings.base import SMS_CODE_LENGTH

errors_dict = {'4000': 'phone number must be digit',
               '4001': 'phone number must have at least 10 digits',
               '4002': f'valid verification code must have {SMS_CODE_LENGTH} digits',
               '4003': 'invalid verification code',
               '4004': {'msg': 'a user already submitted with this phone number', 'params': 1},
               '4005': 'verification code expired',
               '4006': 'user not submitted with given credentials',
               '4007': 'no credentials were provided',
               '4008': 'no user found with given phone number',
               '4009': 'either your credentials were wrong or your account has been deactivated',
               '4010': 'this institute is has not been approved yet',
               '4011': 'this user already has a studentship',
               '4012': 'grade must be between 0 and 12',
               '4013': 'major is required for high school students',
               '4014': 'non-high school students can\'t have major',
               '4015': 'college students must enter their studying degree',


               '5000': 'sending SMS failed'}


def serialize_error(code, params=dict(), is_field_error=True):
    msg = errors_dict.get(code, None)
    if type(msg) == str:
        returned = {'code': code, 'detail': msg}
    elif type(msg) == dict:
        returned = {'code': code, 'detail': msg['msg'], **params}
    else:
        returned = {'code': code, 'detail': ''}

    if is_field_error:
        return returned
    else:
        return {'non_field_errors': [returned]}


class MyValidationError(ValidationError):
    def __init__(self, params):
        super().__init__(params)
        if isinstance(self.detail, list):
            self.detail = self.detail[0]
