"""20220907_availabilities_added

Revision ID: 2541b80fb8c8
Revises: bbd1a8d93b63
Create Date: 2022-09-07 20:58:49.622939

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2541b80fb8c8'
down_revision = 'bbd1a8d93b63'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Availability',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('artist_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=True),
    sa.Column('status', sa.Enum('searching', 'booked', name='status'), nullable=True),
    sa.Column('show_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['artist_id'], ['Artist.id'], name=op.f('fk_Availability_artist_id_Artist'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['show_id'], ['Show.id'], name=op.f('fk_Availability_show_id_Show'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_Availability'))
    )
    op.drop_constraint('fk_Show_venue_id_Venue', 'Show', type_='foreignkey')
    op.drop_constraint('fk_Show_artist_id_Artist', 'Show', type_='foreignkey')
    op.create_foreign_key(op.f('fk_Show_venue_id_Venue'), 'Show', 'Venue', ['venue_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_Show_artist_id_Artist'), 'Show', 'Artist', ['artist_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('fk_Show_artist_id_Artist'), 'Show', type_='foreignkey')
    op.drop_constraint(op.f('fk_Show_venue_id_Venue'), 'Show', type_='foreignkey')
    op.create_foreign_key('fk_Show_artist_id_Artist', 'Show', 'Artist', ['artist_id'], ['id'])
    op.create_foreign_key('fk_Show_venue_id_Venue', 'Show', 'Venue', ['venue_id'], ['id'])
    op.drop_table('Availability')
    # ### end Alembic commands ###