"""Rentals page: items you lend or have rented. Shares its layout with Gigs
(views/components/transactions.py)."""
from models.transaction import TransactionKind
from views.components.transactions import render_transactions

render_transactions(TransactionKind.RENTAL)
