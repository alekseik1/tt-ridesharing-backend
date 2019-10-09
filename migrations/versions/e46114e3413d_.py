"""empty message

Revision ID: e46114e3413d
Revises: 
Create Date: 2019-10-04 22:58:34.833435

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e46114e3413d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=40), nullable=False),
    sa.Column('surname', sa.String(length=40), nullable=False),
    sa.Column('email', sa.String(length=256), nullable=False),
    sa.Column('photo', sa.String(length=2000), nullable=True),
    sa.Column('is_trusful', sa.Boolean(), nullable=True),
    sa.Column('password_hash', sa.String(length=94), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('driver',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('passport_1', sa.String(length=2000), nullable=False),
    sa.Column('passport_2', sa.String(length=2000), nullable=False),
    sa.Column('passport_selfie', sa.String(length=2000), nullable=False),
    sa.Column('driver_license_1', sa.String(length=2000), nullable=False),
    sa.Column('driver_license_2', sa.String(length=2000), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('driver')
    op.drop_table('users')
    # ### end Alembic commands ###