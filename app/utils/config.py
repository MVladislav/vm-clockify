import logging
import sys
from pathlib import Path

# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------

try:
    from starlette.config import Config
except ImportError:
    source_to_install = 'starlette'
    logging.log(logging.CRITICAL, f'Failed to Import {source_to_install}')
    try:
        # choice = input(f'[*] Attempt to Auto-istall {source_to_install}? [y/N]')
        choice = 'y'
    except KeyboardInterrupt:
        logging.log(logging.INFO, 'User Interrupted Choice')
        sys.exit(1)
    if choice.strip().lower()[0] == 'y':
        logging.log(logging.INFO, f'Attempting to Install {source_to_install}')
        sys.stdout.flush()
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", source_to_install])
            from starlette.config import Config
            logging.log(logging.INFO, '[DONE]')
        except Exception:
            logging.log(logging.CRITICAL, '[FAIL]')
            sys.exit(1)
    elif choice.strip().lower()[0] == 'n':
        logging.log(logging.INFO, 'User Denied Auto-install')
        sys.exit(1)
    else:
        logging.log(logging.WARNING, 'Invalid Decision')
        sys.exit(1)


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------

config = Config('.env')

# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------


LICENSE: str = config('LICENSE', default='GNU AGPLv3')
AUTHOR: str = config('AUTHOR', default='MVladislav')
AUTHOR_EMAIL: str = config('AUTHOR_EMAIL', default='info@mvladislav.online')

PROJECT_NAME: str = config('PROJECT_NAME', default='vm_clockify')
ENV_MODE: str = config('ENV_MODE', default='KONS')
VERSION: str = config('VERSION', default='0.0.1')

# NOTICE | SPAM | DEBUG | VERBOSE | INFO | NOTICE | WARNING | SUCCESS | ERROR | CRITICAL
LOGGING_LEVEL: str = config('LOGGING_LEVEL',  default='DEBUG')
LOGGING_VERBOSE: int = config('LOGGING_VERBOSE', cast=int,  default=0)
DEBUG: bool = True if LOGGING_LEVEL == 'DEBUG' or \
    LOGGING_LEVEL == 'VERBOSE' or LOGGING_LEVEL == 'SPAM' else False
DEBUG_RELOAD: bool = True if DEBUG else False

# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------


BASE_PATH: str = config('VM_BASE_PATH', default=f'{Path.home()}/Documents/{PROJECT_NAME}')

# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------

# It is required to do a free registration and create a license key
GEO_LICENSE_KEY: str = config('GEO_LICENSE_KEY',  default=None)
# docs: https://dev.maxmind.com/geoip/geoip2/geolite2/
GEO_LITE_TAR_FILE_URL = f'https://download.maxmind.com/app/geoip_download' \
                        f'?edition_id=GeoLite2-City' \
                        f'&license_key={GEO_LICENSE_KEY}' \
                        f'&suffix=tar.gz'
GEO_DB_FNAME = '/GeoLite2-City.mmdb'
GEO_DB_ZIP_FNAME = '/GeoIP2LiteCity.tar.gz'


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------

CLOCKIFY_API_ENDPOINT: str = config('CLOCKIFY_API_ENDPOINT',  default="https://api.clockify.me/api/v1")
CLOCKIFY_API_KEY: str = config('CLOCKIFY_API_KEY',  default=None)
CLOCKIFY_API_WORKSPACE_ID: str = config('CLOCKIFY_API_WORKSPACE_ID',  default=None)
CLOCKIFY_API_USER_ID: str = config('CLOCKIFY_API_USER_ID',  default=None)
