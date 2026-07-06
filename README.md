# Track Role Bot

Discord 버튼으로 트랙 역할을 자동 부여하는 봇입니다.

## 기능

- `/트랙패널` 명령어로 버튼 패널 생성
- 버튼 클릭 시 해당 트랙 역할 부여
- 기존 트랙 역할은 자동 제거
- 한 사람당 하나의 트랙 역할만 유지

## 명령어

```text
/트랙패널
```

생성되는 버튼:

```text
기보 / 취분 / 컨설 / 보제개 / 디포
```

## Railway Variables

```env
DISCORD_BOT_TOKEN=
GUILD_ID=
ADMIN_ONLY_PANEL=true

TRACK_KIBO_ROLE_ID=
TRACK_CHIBUN_ROLE_ID=
TRACK_CONSULTING_ROLE_ID=
TRACK_BOJE_ROLE_ID=
TRACK_DIPO_ROLE_ID=
```

## Discord 권한

봇 초대 Scope:

```text
bot
applications.commands
```

Bot Permissions:

```text
Manage Roles
View Channels
Send Messages
Use Slash Commands
Embed Links
```

중요: 봇 역할이 트랙 역할보다 위에 있어야 역할 부여가 됩니다.

```text
서버 설정 → 역할 → 봇 역할을 기보/취분/컨설/보제개/디포 역할보다 위로 이동
```

## GitHub 배포

```bash
git init
git add .
git commit -m "feat: add track role bot"
git branch -M main
git remote add origin https://github.com/YOUR_ID/track-role-bot.git
git push -u origin main
```
