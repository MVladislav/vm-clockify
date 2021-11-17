from typing import Union

from starlette.config import Config

# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------

config = Config('.env')
config_project = Config('.env_project')

# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------

PROJECT_NAME: str = config_project('PROJECT_NAME', default='vm_recon')
ENV_MODE: str = config('ENV_MODE', default='KONS')

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


BASE_PATH: str = config('VM_BASE_PATH', default=f'.')

# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------

# It is required to do a free registration and create a license key
GEO_LICENSE_KEY: Union[str, None] = config('GEO_LICENSE_KEY',  default=None)
# docs: https://dev.maxmind.com/geoip/geoip2/geolite2/
GEO_LITE_TAR_FILE_URL = f'https://download.maxmind.com/app/geoip_download' \
                        f'?edition_id=GeoLite2-City' \
                        f'&license_key={GEO_LICENSE_KEY}' \
                        f'&suffix=tar.gz'
# TODO: add legacy
# http://dev.maxmind.com/geoip/legacy/geolite/
GEO_DB_FNAME = '/GeoLite2-City.mmdb'
GEO_DB_ZIP_FNAME = '/GeoIP2LiteCity.tar.gz'


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------

CLOCKIFY_API_ENDPOINT: str = config('CLOCKIFY_API_ENDPOINT',  default='https://api.clockify.me/api/v1')
CLOCKIFY_API_KEY: Union[str, None] = config('CLOCKIFY_API_KEY',  default=None)
CLOCKIFY_API_WORKSPACE_ID: Union[str, None] = config('CLOCKIFY_API_WORKSPACE_ID',  default=None)
CLOCKIFY_API_USER_ID: Union[str, None] = config('CLOCKIFY_API_USER_ID',  default=None)

CLOCKIFY_TMP_FILE: str = 'times'

# base url needed, entered as option on call
YOUTRACK_API_ENDPOINT: Union[str, None] = config('YOUTRACK_API_ENDPOINT',  default=None)
YOUTRACK_API_ENDPOINT_SUFFIX: Union[str, None] = 'youtrack/api'
YOUTRACK_API_KEY: Union[str, None] = config('YOUTRACK_API_KEY',  default=None)
