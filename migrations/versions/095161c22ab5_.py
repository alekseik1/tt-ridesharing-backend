"""empty message

Revision ID: 095161c22ab5
Revises: 91f52796cfc0
Create Date: 2020-03-22 19:28:11.137581

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '095161c22ab5'
down_revision = '91f52796cfc0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('organization', 'address')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('organization', sa.Column('address', sa.VARCHAR(length=600), server_default=sa.text("'undefined'::character varying"), autoincrement=False, nullable=False))
    # ### end Alembic commands ###
