"""empty message

Revision ID: 6ef299380035
Revises: df345f85a645
Create Date: 2020-03-22 16:31:19.415491

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6ef299380035'
down_revision = 'df345f85a645'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('organization', 'address',
               existing_type=sa.VARCHAR(length=600),
               nullable=False)
    op.add_column('ride', sa.Column('submit_date', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ride', 'submit_date')
    op.alter_column('organization', 'address',
               existing_type=sa.VARCHAR(length=600),
               nullable=True)
    # ### end Alembic commands ###