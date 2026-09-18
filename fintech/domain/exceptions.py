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
        super().__init__('El usuario no tiene los campos: '+', '.join(fields))

class NotParamsProvided(Exception):
    def __init__(self, field):
        self.field = field
        super().__init__(f'No se provio un parametro {field} para esta busqueda')

class NotEnoughFunds(Exception):
    def __init__(self, balance, withdrawal_value):
        self.balance = balance
        self.withdrawal_value = withdrawal_value
        super().__init__('Fondos insuficientes')