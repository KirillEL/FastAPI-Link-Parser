"""initial migration

Revision ID: 81707e767800
Revises: 
Create Date: 2024-10-21 20:53:53.429621

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81707e767800'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('urllist',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('url')
    )
    op.create_index(op.f('ix_urllist_id'), 'urllist', ['id'], unique=False)
    op.create_table('wordlist',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('word', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wordlist_id'), 'wordlist', ['id'], unique=False)
    op.create_table('linkbetweenurl',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fk_fromurl_id', sa.Integer(), nullable=False),
    sa.Column('fk_tourl_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['fk_fromurl_id'], ['urllist.id'], ),
    sa.ForeignKeyConstraint(['fk_tourl_id'], ['urllist.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_linkbetweenurl_id'), 'linkbetweenurl', ['id'], unique=False)
    op.create_table('wordlocation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fk_word_id', sa.Integer(), nullable=False),
    sa.Column('fk_url_id', sa.Integer(), nullable=False),
    sa.Column('location', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['fk_url_id'], ['urllist.id'], ),
    sa.ForeignKeyConstraint(['fk_word_id'], ['wordlist.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wordlocation_id'), 'wordlocation', ['id'], unique=False)
    op.create_table('linkword',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fk_word_id', sa.Integer(), nullable=False),
    sa.Column('fk_link_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['fk_link_id'], ['linkbetweenurl.id'], ),
    sa.ForeignKeyConstraint(['fk_word_id'], ['wordlist.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_linkword_id'), 'linkword', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_linkword_id'), table_name='linkword')
    op.drop_table('linkword')
    op.drop_index(op.f('ix_wordlocation_id'), table_name='wordlocation')
    op.drop_table('wordlocation')
    op.drop_index(op.f('ix_linkbetweenurl_id'), table_name='linkbetweenurl')
    op.drop_table('linkbetweenurl')
    op.drop_index(op.f('ix_wordlist_id'), table_name='wordlist')
    op.drop_table('wordlist')
    op.drop_index(op.f('ix_urllist_id'), table_name='urllist')
    op.drop_table('urllist')
    # ### end Alembic commands ###
