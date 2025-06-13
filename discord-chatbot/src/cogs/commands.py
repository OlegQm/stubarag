import discord

from src.utils import conversations
from common.logging.global_logger import logger


async def help_command(interaction: discord.Interaction) -> None:
    """
    Sends a help message to the user DM.

    Args:
        - interaction (discord.ext.commands.Context): The context object

    Returns:
        None
    """

    if interaction.guild:
        logger.info(f'[{interaction.guild.name}][{interaction.channel.name}][{interaction.user.name}]')
    else:
        logger.info(f'[DM][{interaction.user.name}]')
    await interaction.response.send_message(
                """
                Nápoveda:
                - **@AgentKovac** - označ ma v správe a ja odpoviem
                - **@AgentKovac in Thread** - označ ma v threade a odpoviem + vezmem do úvahy predchádzajúce správy
                - **/msg question** - odpoviem na tvoju otázku do DM
                - **/help** - zobrazí túto správu
                - **DM** - môžeš mi poslať správu priamo do DM a ja odpoviem
                """, 
                ephemeral=True, 
                delete_after=60
            )


async def msg_command(interaction: discord.Interaction, question: str) -> None:
    """
    DMs the user with a response to question.

    Args:
        - interaction (discord.ext.commands.Context): The context object
        - question (str): User prmpmt for the bot

    Returns:
        None
    """

    if interaction.guild:
        logger.info(f'[{interaction.guild.name}][{interaction.channel.name}][{interaction.user.name}]: "{question}"')
    else:
        logger.info(f'[DM][{interaction.user.name}]: "{question}"')
    await interaction.response.defer(ephemeral=True, thinking=True)
    conversation_context = [{"role": "user", "content": question}]
    ai_response = await conversations.get_response(conversation_context)
    await interaction.user.send(ai_response)
    conversation_context.append({"role": "assistant", "content": ai_response})
    conversations.save_message(conversation_context, interaction.user.name)  
    await interaction.delete_original_response()
