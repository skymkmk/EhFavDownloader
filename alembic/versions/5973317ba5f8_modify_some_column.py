"""Modify some column

Revision ID: 5973317ba5f8
Revises: f06f1b8d9237
Create Date: 2023-06-06 11:09:34.336275

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5973317ba5f8'
down_revision = 'f06f1b8d9237'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('doujinshi', sa.Column('publisher', sa.TEXT(), nullable=True))
    op.add_column('doujinshi', sa.Column('tag', sa.TEXT(), nullable=True))
    op.add_column('doujinshi', sa.Column('language', sa.TEXT(), nullable=True))
    op.add_column('doujinshi', sa.Column('publish_time', sa.TEXT(), nullable=True))
    op.drop_column('doujinshi', 'parent_gid')
    op.drop_column('doujinshi', 'current_gid')
    op.drop_column('doujinshi', 'current_key')
    op.drop_column('doujinshi', 'parent_key')
    op.drop_column('doujinshi', 'first_gid')
    op.drop_column('doujinshi', 'first_key')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('doujinshi', sa.Column('first_key', sa.TEXT(), nullable=True))
    op.add_column('doujinshi', sa.Column('first_gid', sa.INTEGER(), nullable=True))
    op.add_column('doujinshi', sa.Column('parent_key', sa.TEXT(), nullable=True))
    op.add_column('doujinshi', sa.Column('current_key', sa.TEXT(), nullable=True))
    op.add_column('doujinshi', sa.Column('current_gid', sa.INTEGER(), nullable=True))
    op.add_column('doujinshi', sa.Column('parent_gid', sa.INTEGER(), nullable=True))
    op.drop_column('doujinshi', 'language')
    op.drop_column('doujinshi', 'tag')
    op.drop_column('doujinshi', 'publisher')
    op.drop_column('doujinshi', 'publish_time')
    # ### end Alembic commands ###
