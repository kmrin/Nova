from discord import Interaction, Embed, ButtonStyle
from discord.ui import View, Button, button as btn
from typing import Optional

from ..managers.locale import get_interaction_locale, get_localised_string


class DefaultConfirmation(View):
    def __init__(self, interaction: Interaction, confirm_embed: Embed, cancel_embed: Embed):
        super().__init__(timeout=60.0)
        self.interaction = interaction
        self.confirm_embed = confirm_embed
        self.cancel_embed = cancel_embed
        self.value: Optional[bool] = None
        
        locale = get_interaction_locale(interaction)
        
        self.confirm_button.label = get_localised_string(locale, "ui_button_confirm")
        self.cancel_button.label = get_localised_string(locale, "ui_button_cancel")
    
    @btn(style=ButtonStyle.green)
    async def confirm_button(self, interaction: Interaction, button: Button):
        self.value = True
        self.clear_items()
        
        await interaction.response.edit_message(embed=self.confirm_embed, view=self)
        
        self.stop()
    
    @btn(style=ButtonStyle.red)
    async def cancel_button(self, interaction: Interaction, button: Button):
        self.value = False
        self.clear_items()
        
        await interaction.response.edit_message(embed=self.cancel_embed, view=self)
        
        self.stop()
    
    async def on_timeout(self):
        self.stop()