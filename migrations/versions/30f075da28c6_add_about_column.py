"""add_about_column

Revision ID: 30f075da28c6
Revises: 8d91225d3d34
Create Date: 2020-05-13 14:15:07.484699

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '30f075da28c6'
down_revision = '8d91225d3d34'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('about', sa.String(length=400), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'about')
    # ### end Alembic commands ###
