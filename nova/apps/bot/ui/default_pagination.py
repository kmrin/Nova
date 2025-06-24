from discord import Interaction, Embed, ButtonStyle
from discord.ui import View, Button, button as btn


class DefaultPagination(View):
    def __init__(self, embed: Embed, chunks: list, current_chunk: int = 0) -> None:
        super().__init__(timeout=None)
        
        self.embed = embed
        self.chunks = chunks
        self.curr_chunk = current_chunk
        self.max_chunk = len(chunks) - 1
        
        self.page.label = f"{self.curr_chunk + 1}/{self.max_chunk + 1}"
    
    def __update_button_states(self) -> None:
        self.page.label = f'{self.curr_chunk + 1}/{self.max_chunk + 1}'

        # Page is at starting point
        if self.curr_chunk == 0:
            self.home.disabled = True
            self.prev.disabled = True
            self.next.disabled = False
            self.end.disabled = False

        # Page is between min and max
        if 0 < self.curr_chunk < self.max_chunk:
            self.home.disabled = False
            self.prev.disabled = False
            self.next.disabled = False
            self.end.disabled = False

        # Page is at max point
        if self.curr_chunk == self.max_chunk:
            self.home.disabled = False
            self.prev.disabled = False
            self.next.disabled = True
            self.end.disabled = True

    @btn(label="⏪", style=ButtonStyle.blurple, custom_id="home", disabled=True)
    async def home(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.defer()

        self.curr_chunk = 0
        self.embed.description = "\n".join(self.chunks[self.curr_chunk])
        self.__update_button_states()

        await interaction.edit_original_response(embed=self.embed, view=self)

    @btn(label="◀️", style=ButtonStyle.green, custom_id="prev", disabled=True)
    async def prev(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.defer()

        if not self.curr_chunk == 0:
            self.curr_chunk -= 1

        self.embed.description = "\n".join(self.chunks[self.curr_chunk])
        self.__update_button_states()

        await interaction.edit_original_response(embed=self.embed, view=self)

    @btn(label="", style=ButtonStyle.grey, custom_id="page", disabled=True)
    async def page(self, interaction: Interaction, button: Button) -> None:
        pass

    @btn(label="▶️", style=ButtonStyle.green, custom_id="next")
    async def next(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.defer()

        if not self.curr_chunk == self.max_chunk:
            self.curr_chunk += 1

        self.embed.description = "\n".join(self.chunks[self.curr_chunk])
        self.__update_button_states()

        await interaction.edit_original_response(embed=self.embed, view=self)

    @btn(label="⏩", style=ButtonStyle.blurple, custom_id="end")
    async def end(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.defer()

        self.curr_chunk = self.max_chunk
        self.embed.description = "\n".join(self.chunks[self.curr_chunk])
        self.__update_button_states()

        await interaction.edit_original_response(embed=self.embed, view=self)