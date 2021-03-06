"""empty message

Revision ID: 8d91225d3d34
Revises: ddd17b9f11b3
Create Date: 2020-04-20 23:54:23.209771

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8d91225d3d34'
down_revision = 'ddd17b9f11b3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ride', sa.Column('from_organization', sa.Boolean(), nullable=False))
    op.add_column('ride', sa.Column('latitude', sa.Float(), nullable=False))
    op.add_column('ride', sa.Column('longitude', sa.Float(), nullable=False))
    op.add_column('ride', sa.Column('organization_id', sa.Integer(), nullable=False))
    op.drop_constraint('fk_ride_start_organization_id_organization', 'ride', type_='foreignkey')
    op.create_foreign_key(op.f('fk_ride_organization_id_organization'), 'ride', 'organization', ['organization_id'], ['id'])
    op.drop_column('ride', 'stop_latitude')
    op.drop_column('ride', 'stop_longitude')
    op.drop_column('ride', 'start_organization_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ride', sa.Column('start_organization_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.add_column('ride', sa.Column('stop_longitude', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False))
    op.add_column('ride', sa.Column('stop_latitude', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False))
    op.drop_constraint(op.f('fk_ride_organization_id_organization'), 'ride', type_='foreignkey')
    op.create_foreign_key('fk_ride_start_organization_id_organization', 'ride', 'organization', ['start_organization_id'], ['id'])
    op.drop_column('ride', 'organization_id')
    op.drop_column('ride', 'longitude')
    op.drop_column('ride', 'latitude')
    op.drop_column('ride', 'from_organization')
    # ### end Alembic commands ###
