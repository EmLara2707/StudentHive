"""Gigs page: services and projects you provide or have booked. Shares its layout
with Rentals (views/components/transactions.py)."""
from models.transaction import TransactionKind
from views.components.transactions import render_transactions

render_transactions(TransactionKind.GIG)
