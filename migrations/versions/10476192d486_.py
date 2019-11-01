"""empty message

Revision ID: 10476192d486
Revises: 015c71bba2f1
Create Date: 2019-11-01 02:51:59.601607

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '10476192d486'
down_revision = '015c71bba2f1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ride', sa.Column('is_finished', sa.Boolean(), server_default='false', nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ride', 'is_finished')
    # ### end Alembic commands ###
