from classes.typed_dictionaries import DiscordCommandDict, DiscordCommandDictAttribute
from classes.data_classes import GlobalVars
from typing import List

def get_commands(glob: GlobalVars) -> List[DiscordCommandDict]:
    """
    Returns dictionary with commands

    :param glob: GlobalVars object
    :return: dict
    """
    command_list: List[DiscordCommandDict] = []
    for command in glob.bot.commands:
        if command.hidden:
            continue

        attrs: List[DiscordCommandDictAttribute] = []
        # noinspection PyProtectedMember
        for key, value in command.app_command._params.items():
            attrs.append({
                'name': key,
                'description': str(value.description),
                'required': value.required,
                'default': str(value.default),
                'type': str(value.type)
            })

        command_dict = {
            'name': command.name,
            'description': str(command.description),
            'category': command.extras.get('category', 'No category'),
            'attributes': attrs
        }

        command_list.append(command_dict)

    return command_list
