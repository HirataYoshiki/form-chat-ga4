from typing import List, Optional, Dict, Any
from datetime import date, datetime, time
from sqlalchemy import func, Table, Column, MetaData, String, DateTime, Text # Added Text for message, email, name
from sqlalchemy.orm import Session
from sqlalchemy.sql.sqltypes import TIMESTAMPTZ # For created_at

# Define a MetaData object. In a larger application, this might be shared.
metadata = MetaData()

# Define the contact_submissions table structure explicitly for use in queries.
# This should ideally match the actual schema defined in contact_form_schema.sql.
contact_submissions_table = Table(
    'contact_submissions', metadata,
    Column('id', DateTime, primary_key=True), # Assuming some primary key, BIGSERIAL implies integer but mapped to DateTime for example
    Column('created_at', TIMESTAMPTZ, default=func.now()), # Use TIMESTAMPTZ
    Column('name', Text), # Changed to Text
    Column('email', Text), # Changed to Text
    Column('message', Text), # Changed to Text
    Column('ga_client_id', Text, nullable=True),
    Column('ga_session_id', Text, nullable=True),
    Column('form_id', Text, nullable=True) # Changed to Text
)

def get_submissions_count(
    db: Session,
    start_date: Optional[date],
    end_date: Optional[date],
    form_id: Optional[str]
) -> int:
    """
    Retrieves the count of contact submissions based on the given filters.
    `db` is expected to be a SQLAlchemy Session.
    `start_date` and `end_date` are date objects.
    `form_id` is a string.
    """
    query = db.query(func.count(contact_submissions_table.c.id))

    if start_date:
        start_datetime = datetime.combine(start_date, time.min)
        query = query.filter(contact_submissions_table.c.created_at >= start_datetime)

    if end_date:
        end_datetime = datetime.combine(end_date, time.max)
        query = query.filter(contact_submissions_table.c.created_at <= end_datetime)

    if form_id:
        query = query.filter(contact_submissions_table.c.form_id == form_id)

    count = query.scalar_one_or_none() # Use scalar_one_or_none to handle cases where no rows match
    return count if count is not None else 0

def get_summary_by_form(db: Session) -> List[Dict[str, Any]]:
    """
    Retrieves a summary of submission counts grouped by form_id.
    `db` is expected to be a SQLAlchemy Session.
    Returns a list of dictionaries, e.g., [{"form_id": "form_A", "count": 10}, ...].
    """
    query = db.query(
        contact_submissions_table.c.form_id,
        func.count(contact_submissions_table.c.id).label('count')
    ).group_by(contact_submissions_table.c.form_id).order_by(contact_submissions_table.c.form_id)

    results = query.all()

    # Convert RowProxy objects (or similar, depending on SQLAlchemy version) to dictionaries
    summary_list = []
    for row in results:
        # Access columns by their actual names or keys
        # Assuming row is a KeyedTuple (SQLAlchemy 1.4+) or similar RowProxy
        current_form_id = getattr(row, 'form_id', None) # Or row['form_id']
        current_count = getattr(row, 'count', 0)       # Or row['count']
        summary_list.append({
            "form_id": current_form_id if current_form_id is not None else "N/A",
            "count": current_count
        })
    return summary_list
