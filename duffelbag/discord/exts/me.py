"""Bot plugin for showing the user their Arknights account's infomation."""

import disnake
from arkprts import Client, YostarAuth
from disnake.ext import plugins

import database
from duffelbag import auth

plugin = plugins.Plugin()

@plugin.slash_command()
async def me(inter: disnake.CommandInteraction) -> None:
    """Get your Arknights account's general information."""
    join = database.ArknightsUser.user.join_on(database.PlatformUser.user)
    user = await database.ArknightsUser.objects().where((join.platform_id == inter.author.id) & (join.platform_name == auth.Platform.DISCORD)).first()
    if not user:
        await inter.send("Cannot find a user, ensure that you've made a user and linked them to your arknights account")
        return
    await inter.response.defer()
    client_auth = YostarAuth()
    await client_auth.login_with_token(user.channel_uid, user.yostar_token)
    client = Client(client_auth, assets=False)
    data = await client.get_data()
    operators = []
    for operator in data.social.assist_char_list:
        assert operator
        troop_data = data.troop.chars[operator.char_inst_id]
        operator_data = await database.Character.objects().where(database.Character.id == troop_data.char_id).first()
        assert operator_data
        skill = troop_data.skills[operator.skill_index]
        skill_level = f"m{skill.specialize_level}" if skill.specialize_level > 0 else f"l{troop_data.main_skill_lvl}"
        operators.append(f"- {operator_data.name} e{troop_data.evolve_phase}{troop_data.level} s{operator.skill_index}l{skill_level}")
    operators = "\n".join(operators)
    await inter.send(f"{data.status.nickname} lvl{data.status.level}\nSupport operators:\n{operators}")

setup, teardown = plugin.create_extension_handlers()
