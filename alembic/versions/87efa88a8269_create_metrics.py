"""create metrics

Revision ID: 87efa88a8269
Revises: 40cafcbf74b1
Create Date: 2024-11-16 09:39:22.889014

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87efa88a8269'
down_revision: Union[str, None] = '40cafcbf74b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('''
    create table if not exists metrics (
    id serial constraint metrics_pk primary key,
    url_id integer constraint metrics_urllist_fk
        references urllist,
    metric_freq integer not null,
    metric_pagerank float not null,
    normal_metric_freq float,
    normal_metric_pagerank float,
    result_metric float
    );
    ''')


def downgrade() -> None:
    op.execute('''
    drop table if exists metrics;
    ''')
