from app.models import RecurringTransaction, Transaction
from app.schemas.attachments import AttachmentOut
from app.schemas.recurring_transactions import RecurringTransactionOut
from app.schemas.transactions import RefOut, TransactionOut


def transaction_to_out(transaction: Transaction) -> TransactionOut:
    return TransactionOut(
        id=transaction.id,
        user_id=transaction.user_id,
        wallet=RefOut(
            id=transaction.wallet.id,
            name=transaction.wallet.name,
            type=transaction.wallet.type,
        ),
        category=RefOut(
            id=transaction.category.id,
            name=transaction.category.name,
            type=transaction.category.type,
        ),
        payment_method=RefOut(
            id=transaction.payment_method.id,
            name=transaction.payment_method.name,
            type=transaction.payment_method.type,
        ),
        type=transaction.type,
        amount=transaction.amount,
        currency_code=transaction.currency_code,
        title=transaction.title,
        description=transaction.description,
        transaction_date=transaction.transaction_date,
        tags=[transaction_tag.tag.name for transaction_tag in transaction.transaction_tags],
        attachments=[
            AttachmentOut.model_validate(attachment) for attachment in transaction.attachments
        ],
        is_deleted=transaction.is_deleted,
        created_at=transaction.created_at,
        updated_at=transaction.updated_at,
    )


def recurring_transaction_to_out(recurring: RecurringTransaction) -> RecurringTransactionOut:
    return RecurringTransactionOut(
        id=recurring.id,
        user_id=recurring.user_id,
        wallet=RefOut(id=recurring.wallet.id, name=recurring.wallet.name, type=recurring.wallet.type),
        category=RefOut(
            id=recurring.category.id,
            name=recurring.category.name,
            type=recurring.category.type,
        ),
        type=recurring.type,
        amount=recurring.amount,
        currency_code=recurring.currency_code,
        title=recurring.title,
        description=recurring.description,
        frequency=recurring.frequency,
        start_date=recurring.start_date,
        end_date=recurring.end_date,
        next_run_date=recurring.next_run_date,
        is_active=recurring.is_active,
        created_at=recurring.created_at,
        updated_at=recurring.updated_at,
    )
