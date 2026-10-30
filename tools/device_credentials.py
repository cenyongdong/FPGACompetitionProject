"""Read owner-managed local credentials without putting secrets in Git or logs."""
import getpass
import json
from pathlib import Path


PRIVATE_CONFIG = Path(__file__).resolve().parents[1] / '.local/device-access.private.json'


def credentials(host, default_user):
    """Use an ignored local entry, or request the password with hidden input."""
    if PRIVATE_CONFIG.exists():
        try:
            entry = json.loads(PRIVATE_CONFIG.read_text(encoding='utf-8-sig')).get(host)
            if entry is not None:
                user, password = entry['username'], entry['password']
                if not isinstance(user, str) or not isinstance(password, str) or not user or not password:
                    raise ValueError()
                return user, password
        except (ValueError, KeyError, TypeError, AttributeError):
            # Never include the parsed contents or the underlying exception text.
            raise ValueError('Invalid local device credential configuration') from None
    password = getpass.getpass(f'Password for {default_user}@{host} (hidden): ')
    if not password:
        raise ValueError('Empty device password refused')
    return default_user, password
