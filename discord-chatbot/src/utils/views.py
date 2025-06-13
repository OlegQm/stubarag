import discord

class ButtonsView(discord.ui.View):
    """
    A view with buttons for user interaction.
    This view contains buttons for starting a new conversation and giving feedback (thumbs up/down).
    """

    def __init__(self):
        """
        Initializes the ButtonsView.
        """
        super().__init__()
    

    @discord.ui.button(label="New Conversation", style=discord.ButtonStyle.primary, emoji="💬")
    async def new_conversation(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Button to start a new conversation.

        Args:
            - interaction (discord.Interaction): The interaction object
            - button (discord.ui.Button): The button object
        
        Returns:
            None
        """
        embed = discord.Embed(description="~~        ~~ START OF NEW CONVERSATION ~~        ~~")
        await interaction.response.send_message(embed=embed)
        self.stop()


    @discord.ui.button(label="👍", style=discord.ButtonStyle.success)
    async def thumbs_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Button to give a positive feedback to conversation.

        Args:
            - interaction (discord.Interaction): The interaction object
            - button (discord.ui.Button): The button object

        Returns:
            None
        """
        await interaction.response.send_message("Ďakujem za spätnú väzbu ! Pomáhaš mi tak stále sa zlepšovať :-)")
        self.stop()
        

    @discord.ui.button(label="👎", style=discord.ButtonStyle.danger)
    async def thumbs_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Button to give a negative feedback to conversation.

        Args:
            - interaction (discord.Interaction): The interaction object
            - button (discord.ui.Button): The button object

        Returns:
            None
        """
        await interaction.response.send_message("Ďakujem za spätnú väzbu ! Pomáhaš mi tak stále sa zlepšovať :-)")
        self.stop()
