from django.db import models
from .user import User

class Transaction(models.Model):
    class TransactionTypes(models.TextChoices):
        DEPOSIT = 'DEPOSIT'
        WITHDRAWAL = 'WITHDRAWAL'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(
        choices=TransactionTypes
    )