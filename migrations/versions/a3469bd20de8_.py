"""empty message

Revision ID: a3469bd20de8
Revises: 04191bd734be
Create Date: 2019-10-30 00:32:57.584819

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3469bd20de8'
down_revision = '04191bd734be'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('driver', 'passport_1')
    op.drop_column('driver', 'passport_selfie')
    op.drop_column('driver', 'passport_2')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('driver', sa.Column('passport_2', sa.VARCHAR(length=2000), autoincrement=False, nullable=False))
    op.add_column('driver', sa.Column('passport_selfie', sa.VARCHAR(length=2000), autoincrement=False, nullable=False))
    op.add_column('driver', sa.Column('passport_1', sa.VARCHAR(length=2000), autoincrement=False, nullable=False))
    # ### end Alembic commands ###