from enum import StrEnum


class WalletType(StrEnum):
    CASH = "CASH"
    BANK = "BANK"
    MOBILE_BANKING = "MOBILE_BANKING"
    CARD = "CARD"
    SAVINGS = "SAVINGS"
    INVESTMENT = "INVESTMENT"


class CategoryType(StrEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class PaymentMethodType(StrEnum):
    CASH = "CASH"
    CARD = "CARD"
    BANK_TRANSFER = "BANK_TRANSFER"
    MOBILE_BANKING = "MOBILE_BANKING"
    OTHER = "OTHER"


class TransactionType(StrEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"


class RecurringFrequency(StrEnum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"
