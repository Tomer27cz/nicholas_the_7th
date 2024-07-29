"""add voice_logs

Revision ID: bbbcfd8e8176
Revises: 70328dfea790
Create Date: 2024-07-22 15:06:46.865845

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bbbcfd8e8176'
down_revision: Union[str, None] = '70328dfea790'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('voice_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('guild_id', sa.Integer(), nullable=True),
    sa.Column('channel_id', sa.Integer(), nullable=True),
    sa.Column('connected_at', sa.Integer(), nullable=True),
    sa.Column('disconnected_at', sa.Integer(), nullable=True),
    sa.Column('time_in_vc', sa.Integer(), nullable=True),
    sa.Column('time_playing', sa.Integer(), nullable=True),
    sa.Column('time_paused', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('voice_logs')
    # ### end Alembic commands ###