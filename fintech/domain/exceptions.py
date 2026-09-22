class UserNotFound(Exception):
    def __init__(self, value: str | int, param: str):
        self.param = param
        self.value = value
        super().__init__(f'the user with {param} {value} was not found')

class EmailIsRegistered(Exception):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f'the email {email} is already registered')

class NotAValidUser(Exception):
    def __init__(self, fields: list):
        self.fields = fields
        super().__init__('the user does not have the fields: '+', '.join(fields))

class NotParamsProvided(Exception):
    def __init__(self, field):
        self.field = field
        super().__init__(f'A param {field} was not provided to do this search')

class NotEnoughFunds(Exception):
    def __init__(self, balance, withdrawal_value):
        self.balance = balance
        self.withdrawal_value = withdrawal_value
        super().__init__('Not enough funds')

class NotAValidValue(Exception):
    def __init__(self, value, key, cause=''):
        self.value = value
        self.key = key
        self.cause = cause
        message = f'the param {key}, with value {value}, it is not valid'
        if len(cause):
            message += f' because {cause}'
        super().__init__(message)