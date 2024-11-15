"""add matchrows

Revision ID: 40cafcbf74b1
Revises: 81707e767800
Create Date: 2024-11-15 20:02:12.562446

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40cafcbf74b1'
down_revision: Union[str, None] = '81707e767800'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('''
    create table matchrows (
    id serial constraint matchrows_pk primary key,
    url_id integer constraint matchrows_url_urllist_fk
        references urllist,
    loc_word1 integer not null,
    loc_word2 integer not null
    );
    ''')


def downgrade() -> None:
    op.execute('''
    drop table if not exists matchrows;
    ''')
