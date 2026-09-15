class UserNotFound(Exception):
    def __init__(self, value: str | int, param: str):
        self.param = param
        self.value = value
        super().__init__(f'the user with {param} {value} was not found')