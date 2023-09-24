"""Bot plugin for showing the user their Arknights account's infomation."""

import io

import disnake
from arkprts import Client, NetworkSession, YostarAuth
from disnake.ext import plugins
from PIL import Image

import database
from duffelbag import auth

plugin = plugins.Plugin()


@plugin.slash_command()
async def me(inter: disnake.CommandInteraction, *, private: bool = True) -> None:
    """Get your Arknights account's general information."""
    join = database.ArknightsUser.user.join_on(database.PlatformUser.user)
    user = (
        await database.ArknightsUser.objects()
        .where(
            (join.platform_id == inter.author.id) & (join.platform_name == auth.Platform.DISCORD),
        )
        .first()
    )
    if not user:
        await inter.send(
            "Cannot find a user, ensure that you've made a user and linked"
            " them to your arknights account",
            ephemeral=True,
        )
        return
    await inter.response.defer(ephemeral=private)

    client_auth = YostarAuth()
    await client_auth.login_with_token(user.channel_uid, user.yostar_token)
    client = Client(client_auth, assets=False)
    data = await client.get_data()

    embed = disnake.Embed(
        title=f"{data.status.nickname} lv{data.status.level}",
        description=f"*{data.status.resume}*",
    )
    secretary_skin =  data.status.secretary_skin_id.replace("@", "_").replace("#", "%23") if "@" in data.status.secretary_skin_id else data.status.secretary_skin_id.replace("#", "_")
    embed.set_thumbnail(
        "https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/avatar/" # I hate myself
        f"{secretary_skin}.png",
    )

    chars = []
    for operator in data.social.assist_char_list:
        assert operator
        troop_data = data.troop.chars[operator.char_inst_id]
        chars.append(troop_data.skin)
        operator_data = (
            await database.Character.objects()
            .where(database.Character.id == troop_data.char_id)
            .first()
        )
        assert operator_data
        skill = troop_data.skills[operator.skill_index]
        skill_level = (
            f"m{skill.specialize_level}"
            if skill.specialize_level > 0
            else f"l{troop_data.main_skill_lvl}"
        )
        embed.add_field(
            name=f"{operator_data.name}",
            value=f"e{troop_data.evolve_phase}l{troop_data.level}"
            f" s{operator.skill_index}{skill_level}",
        )
    with io.BytesIO() as image_binary:
        display = await display_support(chars, client.network)
        display.save(image_binary, "PNG")
        image_binary.seek(0)
        embed.set_image("attachment://support_operators.png")
        await inter.send(
            embed=embed,
            ephemeral=private,
            file=disnake.File(fp=image_binary, filename="support_operators.png"),
        )
    await client.network.close()

async def display_support(chars: list[str], network: NetworkSession) -> Image.Image:
    """Create an image display of a user's support operators."""
    canvas = Image.new("RGBA", (540, 341))
    for i, char in enumerate(chars):
        char_skin = char.replace("@", "_").replace("#", "%23") if "@" in char else char.replace("#", "_")
        image = Image.open(io.BytesIO(await (await network.session.get(f"https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/portrait/{char_skin}.png")).read()))
        canvas.paste(image, (180 * i, 0))
    return canvas

setup, teardown = plugin.create_extension_handlers()
