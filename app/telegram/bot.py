import logging
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from ..config import settings

logger = logging.getLogger(__name__)

_telegram_client: TelegramClient | None = None

phone_code_hashes = {}


def get_telegram_client() -> TelegramClient | None:
    global _telegram_client

    if not settings.TELEGRAM_API_ID or not settings.TELEGRAM_API_HASH:
        logger.error('Telegram credentials not set')
        return None

    if not _telegram_client:
        _telegram_client = TelegramClient(
            settings.TELEGRAM_SESSION_NAME,
            settings.TELEGRAM_API_ID,
            settings.TELEGRAM_API_HASH
        )
    return _telegram_client


async def authorize_telegram(phone: str, code: str | None = None, password: str | None = None) -> dict:
    if not settings.TELEGRAM_API_ID or not settings.TELEGRAM_API_HASH:
        return {
            'success': False,
            'message': 'Telegram credentials not configured'
        }

    client = TelegramClient(
        settings.TELEGRAM_SESSION_NAME,
        settings.TELEGRAM_API_ID,
        settings.TELEGRAM_API_HASH
    )

    try:
        await client.connect()

        if await client.is_user_authorized():
            me = await client.get_me()
            return {
                'success': True,
                'message': f'Уже авторизован как {me.first_name} {me.last_name or ""}',
                'phone': me.phone,
                'username': me.username
            }

        if not code:
            sent = await client.send_code_request(phone)
            phone_code_hashes[phone] = sent.phone_code_hash  # сохранили hash
            return {
                'success': True,
                'message': 'Код подтверждения отправлен в Telegram',
                'next_step': 'code'
            }

        try:
            phone_code_hash = phone_code_hashes.get(phone)
            if not phone_code_hash:
                return {
                    'success': False,
                    'message': 'Сначала запросите код'
                }

            await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
            me = await client.get_me()
            return {
                'success': True,
                'message': f'Успешно авторизован как {me.first_name} {me.last_name or ""}',
                'phone': me.phone,
                'username': me.username
            }
        except SessionPasswordNeededError:
            if not password:
                return {
                    'success': False,
                    'message': 'Требуется пароль двухфакторной аутентификации',
                    'next_step': 'password'
                }

            await client.sign_in(password=password)
            me = await client.get_me()
            return {
                'success': True,
                'message': f'Успешно авторизован как {me.first_name} {me.last_name or ""}',
                'phone': me.phone,
                'username': me.username
            }

    except Exception as e:
        logger.error(f'Ошибка при авторизации Telegram: {e}', exc_info=True)
        return {
            'success': False,
            'message': f'Ошибка авторизации: {str(e)}'
        }
    finally:
        await client.disconnect()
