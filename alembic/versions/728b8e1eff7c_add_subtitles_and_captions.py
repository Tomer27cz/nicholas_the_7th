"""add subtitles_and_captions

Revision ID: 728b8e1eff7c
Revises: 1a355400242c
Create Date: 2024-07-22 23:14:56.043392

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '728b8e1eff7c'
down_revision: Union[str, None] = '1a355400242c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('history', sa.Column('subtitles', sa.JSON(), nullable=True))
    op.add_column('history', sa.Column('captions', sa.JSON(), nullable=True))
    op.add_column('now_playing', sa.Column('subtitles', sa.JSON(), nullable=True))
    op.add_column('now_playing', sa.Column('captions', sa.JSON(), nullable=True))
    op.add_column('queue', sa.Column('subtitles', sa.JSON(), nullable=True))
    op.add_column('queue', sa.Column('captions', sa.JSON(), nullable=True))
    op.add_column('save_videos', sa.Column('subtitles', sa.JSON(), nullable=True))
    op.add_column('save_videos', sa.Column('captions', sa.JSON(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('save_videos', 'captions')
    op.drop_column('save_videos', 'subtitles')
    op.drop_column('queue', 'captions')
    op.drop_column('queue', 'subtitles')
    op.drop_column('now_playing', 'captions')
    op.drop_column('now_playing', 'subtitles')
    op.drop_column('history', 'captions')
    op.drop_column('history', 'subtitles')
    # ### end Alembic commands ###
