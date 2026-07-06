import os
import logging
from typing import Dict, List

import discord
from discord import app_commands
from discord.ext import commands

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


# =========================
# Config
# =========================

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

ADMIN_ONLY_PANEL = os.getenv("ADMIN_ONLY_PANEL", "true").lower() == "true"

TRACKS: Dict[str, Dict[str, str]] = {
    "kibo": {
        "label": os.getenv("TRACK_KIBO_LABEL", "기보"),
        "role_id": os.getenv("TRACK_KIBO_ROLE_ID", ""),
        "emoji": os.getenv("TRACK_KIBO_EMOJI", "🛡️"),
    },
    "chibun": {
        "label": os.getenv("TRACK_CHIBUN_LABEL", "취분"),
        "role_id": os.getenv("TRACK_CHIBUN_ROLE_ID", ""),
        "emoji": os.getenv("TRACK_CHIBUN_EMOJI", "🔍"),
    },
    "consulting": {
        "label": os.getenv("TRACK_CONSULTING_LABEL", "컨설"),
        "role_id": os.getenv("TRACK_CONSULTING_ROLE_ID", ""),
        "emoji": os.getenv("TRACK_CONSULTING_EMOJI", "📋"),
    },
    "boje": {
        "label": os.getenv("TRACK_BOJE_LABEL", "보제개"),
        "role_id": os.getenv("TRACK_BOJE_ROLE_ID", ""),
        "emoji": os.getenv("TRACK_BOJE_EMOJI", "⚙️"),
    },
    "dipo": {
        "label": os.getenv("TRACK_DIPO_LABEL", "디포"),
        "role_id": os.getenv("TRACK_DIPO_ROLE_ID", ""),
        "emoji": os.getenv("TRACK_DIPO_EMOJI", "🧬"),
    },
}


# =========================
# Logging
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)


# =========================
# Validation
# =========================

def validate_config() -> None:
    if not DISCORD_BOT_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN 환경변수가 없습니다.")

    if not GUILD_ID:
        raise RuntimeError("GUILD_ID 환경변수가 없습니다.")

    missing_roles = []

    for key, item in TRACKS.items():
        if not item["role_id"]:
            missing_roles.append(key)

    if missing_roles:
        raise RuntimeError(
            f"트랙 Role ID가 비어 있습니다: {', '.join(missing_roles)}"
        )


def get_track_role_ids() -> List[int]:
    role_ids = []

    for item in TRACKS.values():
        role_id = item["role_id"]

        if role_id:
            role_ids.append(int(role_id))

    return role_ids


# =========================
# Discord Bot
# =========================

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


class TrackButton(discord.ui.Button):
    def __init__(self, track_key: str, label: str, role_id: int, emoji: str):
        super().__init__(
            label=label,
            emoji=emoji,
            style=discord.ButtonStyle.primary,
            custom_id=f"track_role:{track_key}",
        )

        self.track_key = track_key
        self.track_label = label
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "서버 안에서만 사용할 수 있습니다.",
                ephemeral=True,
            )
            return

        member = interaction.user

        if not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "멤버 정보를 가져오지 못했습니다. 잠시 후 다시 시도해주세요.",
                ephemeral=True,
            )
            return

        guild = interaction.guild
        selected_role = guild.get_role(self.role_id)

        if selected_role is None:
            await interaction.response.send_message(
                f"`{self.track_label}` 역할을 서버에서 찾지 못했습니다. Role ID를 확인해주세요.",
                ephemeral=True,
            )
            return

        track_role_ids = get_track_role_ids()
        roles_to_remove = []

        for role_id in track_role_ids:
            role = guild.get_role(role_id)

            if role and role in member.roles and role.id != selected_role.id:
                roles_to_remove.append(role)

        try:
            if roles_to_remove:
                await member.remove_roles(
                    *roles_to_remove,
                    reason="트랙 역할 변경",
                )

            if selected_role not in member.roles:
                await member.add_roles(
                    selected_role,
                    reason="트랙 역할 선택",
                )

            await interaction.response.send_message(
                f"✅ `{self.track_label}` 트랙 역할이 부여되었습니다.",
                ephemeral=True,
            )

            logger.info(
                "Assigned role. user=%s role=%s removed=%s",
                member,
                selected_role.name,
                [role.name for role in roles_to_remove],
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "권한이 부족해서 역할을 부여하지 못했습니다. "
                "봇 역할이 트랙 역할보다 위에 있는지 확인해주세요.",
                ephemeral=True,
            )

        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"Discord API 오류로 역할 부여에 실패했습니다: `{e}`",
                ephemeral=True,
            )


class TrackRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        for track_key, item in TRACKS.items():
            role_id = item["role_id"]

            if not role_id:
                continue

            self.add_item(
                TrackButton(
                    track_key=track_key,
                    label=item["label"],
                    role_id=int(role_id),
                    emoji=item["emoji"],
                )
            )


@bot.event
async def on_ready() -> None:
    logger.info("Logged in as %s (%s)", bot.user, bot.user.id if bot.user else "unknown")


@bot.event
async def setup_hook() -> None:
    # 봇 재시작 후에도 기존 버튼이 계속 동작하도록 persistent view 등록
    bot.add_view(TrackRoleView())

    guild = discord.Object(id=int(GUILD_ID))
    bot.tree.copy_global_to(guild=guild)
    synced = await bot.tree.sync(guild=guild)
    logger.info("Synced %s commands to guild_id=%s", len(synced), GUILD_ID)


@bot.tree.command(
    name="트랙패널",
    description="트랙 역할 선택 버튼 패널을 생성합니다.",
)
@app_commands.describe(
    title="패널 제목",
    description="패널 설명",
)
async def track_panel(
    interaction: discord.Interaction,
    title: str = "트랙 역할 선택",
    description: str = "아래 버튼 중 본인의 트랙을 선택하면 해당 역할이 자동으로 부여됩니다.",
):
    if ADMIN_ONLY_PANEL:
        if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "이 명령어는 역할 관리 권한이 있는 사람만 사용할 수 있습니다.",
                ephemeral=True,
            )
            return

    embed = discord.Embed(
        title=title,
        description=description,
        color=0x5865F2,
    )

    track_lines = []

    for item in TRACKS.values():
        track_lines.append(f"{item['emoji']} {item['label']}")

    embed.add_field(
        name="선택 가능 트랙",
        value="\n".join(track_lines),
        inline=False,
    )

    embed.set_footer(text="하나의 트랙만 선택됩니다. 다른 트랙을 선택하면 기존 트랙 역할은 제거됩니다.")

    await interaction.response.send_message(
        embed=embed,
        view=TrackRoleView(),
    )


def main() -> None:
    validate_config()
    bot.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
