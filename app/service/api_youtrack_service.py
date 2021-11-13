import json
import logging
import sys
from datetime import datetime
from typing import Dict

import requests

from ..utils.config import YOUTRACK_API_ENDPOINT_SUFFIX
from ..utils.utils import Context, Utils
from .api_clockify_service import IssueTime

# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------


class ApiYoutrackService:

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def __init__(self, ctx: Context):
        if ctx is not None and ctx.utils is not None:
            self.ctx: Context = ctx
            self.utils: Utils = ctx.utils
            logging.log(logging.DEBUG, 'youtrack-api-service is initiated')
        else:
            logging.log(logging.ERROR, "context is not set")
            sys.exit(1)

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    # https://www.jetbrains.com/help/youtrack/devportal/resource-api-issues-issueID-timeTracking-workItems.html#create-IssueWorkItem-method-sample
    def times(self, issues: Dict[str, IssueTime]):
        try:
            format_date_day = '%Y-%m-%d'

            headers = {
                'content-type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.ctx.api_youtrack_key}',
                'Cache-Control': 'no-cache',
            }

            with requests.Session() as session:
                for key, issue in issues.items():
                    if not key.startswith('-> sum:') and issue.date is not None:
                        current_day: datetime = datetime.strptime(issue.date, format_date_day)
                        date = int(current_day.strftime('%s'))*1000
                        description = '\n- '.join(issue.description)
                        description = f'- {description}'

                        body = {
                            'usesMarkdown': True,
                            'date': date,
                            'text': description,
                            'duration': {
                                'presentation': f'{issue.duration.get("h",0)}h {issue.duration.get("m",0)}m'
                            }
                        }
                        if issue.issue_type:
                            body['type'] = {
                                'name': issue.issue_type
                            }

                        if '...' in issue.issue[0]:
                            issue.issue[0] = issue.issue[0].replace('...', input(
                                f'enter number to replace "..." in {issue.issue[0]}: '))

                        path = f'issues/{issue.issue[0]}/timeTracking/workItems'

                        res = session.post(f'{self.ctx.api_youtrack_endpint}/{YOUTRACK_API_ENDPOINT_SUFFIX}/{path}',
                                           headers=headers, json=body)
                        if res.status_code == 200:
                            parsed = json.loads(res.text)
                            logging.log(logging.DEBUG, json.dumps(parsed, indent=4, sort_keys=False))
                        else:
                            logging.log(logging.ERROR, res.status_code)
                            logging.log(logging.ERROR, res.text)

        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)
