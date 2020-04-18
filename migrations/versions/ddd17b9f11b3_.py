"""empty message

Revision ID: ddd17b9f11b3
Revises: 7f8e8343bd70
Create Date: 2020-04-15 00:11:31.220417

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ddd17b9f11b3'
down_revision = '7f8e8343bd70'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ride', sa.Column('start_datetime', sa.DateTime(), nullable=False))
    op.add_column('ride', sa.Column('stop_datetime', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ride', 'stop_datetime')
    op.drop_column('ride', 'start_datetime')
    # ### end Alembic commands ###