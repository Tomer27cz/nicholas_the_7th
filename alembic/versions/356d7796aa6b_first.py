"""first

Revision ID: 356d7796aa6b
Revises: 
Create Date: 2024-03-12 18:13:12.956898

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '356d7796aa6b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('discord_commands',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('category', sa.String(), nullable=True),
    sa.Column('attributes', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('guilds',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('connected', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('guild_data',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('key', sa.CHAR(length=6), nullable=True),
    sa.Column('member_count', sa.Integer(), nullable=True),
    sa.Column('text_channel_count', sa.Integer(), nullable=True),
    sa.Column('voice_channel_count', sa.Integer(), nullable=True),
    sa.Column('role_count', sa.Integer(), nullable=True),
    sa.Column('owner_id', sa.Integer(), nullable=True),
    sa.Column('owner_name', sa.String(), nullable=True),
    sa.Column('created_at', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('large', sa.Boolean(), nullable=True),
    sa.Column('icon', sa.String(), nullable=True),
    sa.Column('banner', sa.String(), nullable=True),
    sa.Column('splash', sa.String(), nullable=True),
    sa.Column('discovery_splash', sa.String(), nullable=True),
    sa.Column('voice_channels', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['guilds.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=True),
    sa.Column('class_type', sa.String(), nullable=True),
    sa.Column('author', sa.String(), nullable=True),
    sa.Column('guild_id', sa.Integer(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('picture', sa.String(), nullable=True),
    sa.Column('duration', sa.String(), nullable=True),
    sa.Column('channel_name', sa.String(), nullable=True),
    sa.Column('channel_link', sa.String(), nullable=True),
    sa.Column('radio_info', sa.JSON(), nullable=True),
    sa.Column('local_number', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.Integer(), nullable=True),
    sa.Column('played_duration', sa.JSON(), nullable=True),
    sa.Column('chapters', sa.JSON(), nullable=True),
    sa.Column('stream_url', sa.String(), nullable=True),
    sa.Column('discord_channel', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('now_playing',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=True),
    sa.Column('class_type', sa.String(), nullable=True),
    sa.Column('author', sa.String(), nullable=True),
    sa.Column('guild_id', sa.Integer(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('picture', sa.String(), nullable=True),
    sa.Column('duration', sa.String(), nullable=True),
    sa.Column('channel_name', sa.String(), nullable=True),
    sa.Column('channel_link', sa.String(), nullable=True),
    sa.Column('radio_info', sa.JSON(), nullable=True),
    sa.Column('local_number', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.Integer(), nullable=True),
    sa.Column('played_duration', sa.JSON(), nullable=True),
    sa.Column('chapters', sa.JSON(), nullable=True),
    sa.Column('stream_url', sa.String(), nullable=True),
    sa.Column('discord_channel', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('options',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('stopped', sa.Boolean(), nullable=True),
    sa.Column('loop', sa.Boolean(), nullable=True),
    sa.Column('is_radio', sa.Boolean(), nullable=True),
    sa.Column('language', sa.String(length=2), nullable=True),
    sa.Column('response_type', sa.String(length=5), nullable=True),
    sa.Column('search_query', sa.String(), nullable=True),
    sa.Column('buttons', sa.Boolean(), nullable=True),
    sa.Column('volume', sa.Float(), nullable=True),
    sa.Column('buffer', sa.Integer(), nullable=True),
    sa.Column('history_length', sa.Integer(), nullable=True),
    sa.Column('last_updated', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['guilds.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('queue',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=True),
    sa.Column('class_type', sa.String(), nullable=True),
    sa.Column('author', sa.String(), nullable=True),
    sa.Column('guild_id', sa.Integer(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('picture', sa.String(), nullable=True),
    sa.Column('duration', sa.String(), nullable=True),
    sa.Column('channel_name', sa.String(), nullable=True),
    sa.Column('channel_link', sa.String(), nullable=True),
    sa.Column('radio_info', sa.JSON(), nullable=True),
    sa.Column('local_number', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.Integer(), nullable=True),
    sa.Column('played_duration', sa.JSON(), nullable=True),
    sa.Column('chapters', sa.JSON(), nullable=True),
    sa.Column('stream_url', sa.String(), nullable=True),
    sa.Column('discord_channel', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('radio_info',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(), nullable=True),
    sa.Column('url', sa.VARCHAR(), nullable=True),
    sa.Column('website', sa.VARCHAR(), nullable=True),
    sa.Column('picture', sa.VARCHAR(), nullable=True),
    sa.Column('channel_name', sa.VARCHAR(), nullable=True),
    sa.Column('title', sa.VARCHAR(), nullable=True),
    sa.Column('last_update', sa.INTEGER(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('saves',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=True),
    sa.Column('guild_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('author_name', sa.String(), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('search_list',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('position', sa.INTEGER(), nullable=True),
    sa.Column('class_type', sa.VARCHAR(), nullable=True),
    sa.Column('author', sa.VARCHAR(), nullable=True),
    sa.Column('guild_id', sa.INTEGER(), nullable=True),
    sa.Column('url', sa.VARCHAR(), nullable=True),
    sa.Column('title', sa.VARCHAR(), nullable=True),
    sa.Column('picture', sa.VARCHAR(), nullable=True),
    sa.Column('duration', sa.VARCHAR(), nullable=True),
    sa.Column('channel_name', sa.VARCHAR(), nullable=True),
    sa.Column('channel_link', sa.VARCHAR(), nullable=True),
    sa.Column('radio_info', sa.JSON(), nullable=True),
    sa.Column('local_number', sa.INTEGER(), nullable=True),
    sa.Column('created_at', sa.INTEGER(), nullable=True),
    sa.Column('played_duration', sa.JSON(), nullable=True),
    sa.Column('chapters', sa.JSON(), nullable=True),
    sa.Column('stream_url', sa.VARCHAR(), nullable=True),
    sa.Column('discord_channel', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('slowed_users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('user_name', sa.String(), nullable=True),
    sa.Column('guild_id', sa.Integer(), nullable=True),
    sa.Column('slowed_for', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tortured_users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('guild_id', sa.Integer(), nullable=True),
    sa.Column('torture_delay', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('save_videos',
    sa.Column('save_id', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=True),
    sa.Column('class_type', sa.String(), nullable=True),
    sa.Column('author', sa.String(), nullable=True),
    sa.Column('guild_id', sa.Integer(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('picture', sa.String(), nullable=True),
    sa.Column('duration', sa.String(), nullable=True),
    sa.Column('channel_name', sa.String(), nullable=True),
    sa.Column('channel_link', sa.String(), nullable=True),
    sa.Column('radio_info', sa.JSON(), nullable=True),
    sa.Column('local_number', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.Integer(), nullable=True),
    sa.Column('played_duration', sa.JSON(), nullable=True),
    sa.Column('chapters', sa.JSON(), nullable=True),
    sa.Column('stream_url', sa.String(), nullable=True),
    sa.Column('discord_channel', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
    sa.ForeignKeyConstraint(['save_id'], ['saves.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('save_videos')
    op.drop_table('tortured_users')
    op.drop_table('slowed_users')
    op.drop_table('saves')
    op.drop_table('queue')
    op.drop_table('options')
    op.drop_table('now_playing')
    op.drop_table('history')
    op.drop_table('guild_data')
    op.drop_table('guilds')
    # ### end Alembic commands ###
