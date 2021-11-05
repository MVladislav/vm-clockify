import json
import logging
import re
from datetime import datetime, timedelta
from typing import List

import requests

from ..utils.utils import Context, Utils

# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------


class ApiService:

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def __init__(self, ctx: Context):
        self.ctx: Context = ctx
        self.utils: Utils = self.ctx.utils
        logging.log(logging.DEBUG, 'test-service is initiated')

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def user(self):
        try:
            headers = {
                'content-type': 'application/json',
                'X-Api-Key': self.ctx.api_key
            }

            with requests.Session() as session:
                res = session.get(f'{self.ctx.api_endpoint}/user', headers=headers)
                parsed = json.loads(res.text)
                logging.log(logging.INFO, f'USER ID             : {parsed["id"]}')
                logging.log(logging.INFO, f'ACTIVE WORKSPACE    : {parsed["activeWorkspace"]}')
                logging.log(logging.INFO, f'DEFAULT WORKSPACE   : {parsed["defaultWorkspace"]}')

                # logging.log(logging.DEBUG, json.dumps(parsed, indent=4, sort_keys=False))
        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)

    def times(self, workspaceId: str, userId: str, days_to_subtract: int = 7, page_size: int = 50):
        try:
            headers = {
                'content-type': 'application/json',
                'X-Api-Key': self.ctx.api_key
            }

            params = {
                'hydrated': True,
                'consider-duration-format': True,
                'page-size': page_size,
                'start': (datetime.now() - timedelta(days=days_to_subtract)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            }

            path = f'workspaces/{workspaceId}/user/{userId}/time-entries'

            prefix_sum = '-> sum:'
            prefix_duration = 'PT'
            # 2021-10-26T13:00:00Z
            format_date_from = '%Y-%m-%dT%H:%M:%SZ'
            format_date_day = '%Y-%m-%d'
            regex_issue = '.*?\[(.*?)\].*?'
            regex_duration = 'PT(?:([0-9]{1,2})H){0,1}(?:([0-9]{1,2})M){0,1}'

            with requests.Session() as session:
                res = session.get(f'{self.ctx.api_endpoint}/{path}', headers=headers, params=params)

                if res.status_code == 200:
                    parsed = json.loads(res.text)
                    results = {}

                    if isinstance(parsed, list):
                        for work in parsed:
                            if isinstance(work, dict):
                                timeStart: str = work.get('timeInterval').get('start')
                                # timeEnd = work.get('timeInterval').get('end')
                                timeDuration: str = work.get('timeInterval').get('duration')
                                current_timeDuration = None
                                if timeDuration.startswith(prefix_duration):
                                    timeDuration_tmp = re.match(regex_duration, timeDuration)
                                    if timeDuration_tmp is not None:
                                        current_timeDuration = {
                                            'h': int(timeDuration_tmp.group(1)) if timeDuration_tmp.group(1) else 0,
                                            'm': int(timeDuration_tmp.group(2)) if timeDuration_tmp.group(2) else 0,
                                        }

                                timeStart = timeStart if not timeStart else datetime.strptime(timeStart, format_date_from)
                                # timeEnd = timeEnd if not timeEnd else datetime.strptime(timeEnd, format_date_from)

                                current_day: str = timeStart.strftime(format_date_day)
                                current_task: str = work.get('task').get('name') if work.get('task') else None
                                current_project: str = work.get('project')['name']
                                current_description: str = work.get('description')

                                # SETUP:: parse issue number from task or project
                                current_issue = re.match(
                                    regex_issue, current_task).group(1) if current_task else re.match(regex_issue, current_project).group(1)

                                # SETUP:: id to store collections combined unique
                                current_id = f'{prefix_sum} {current_day}'
                                # START:: insert or update time per day
                                results[current_id] = results.get(current_id, {})
                                results[current_id]['current_day'] = results[current_id].get('current_day', f'{prefix_sum} {current_day}')
                                if current_timeDuration is not None:
                                    duration: dict = results[current_id].get("duration", {})
                                    duration['h'] = duration.get('h', 0) + current_timeDuration.get('h')
                                    duration['m'] = duration.get('m', 0) + current_timeDuration.get('m')
                                    if duration['m'] >= 60:
                                        new_hour, new_minutes = self.convert_time_split(duration['m']*60)
                                        duration['h'] = duration.get('h', 0) + new_hour
                                        duration['m'] = new_minutes
                                    results[current_id]['duration'] = duration

                                # SETUP:: id to store collections combined unique
                                current_id = f'{current_day}_{current_project}_{current_task}'

                                # START:: insert or update collections
                                results[current_id] = results.get(current_id, {})
                                results[current_id]['current_day'] = results[current_id].get('current_day', current_day)

                                if current_timeDuration is not None:
                                    duration: dict = results[current_id].get("duration", {})
                                    duration['h'] = duration.get('h', 0) + current_timeDuration.get('h')
                                    duration['m'] = duration.get('m', 0) + current_timeDuration.get('m')
                                    if duration['m'] >= 60:
                                        new_hour, new_minutes = self.convert_time_split(duration['m']*60)
                                        duration['h'] = duration.get('h', 0) + new_hour
                                        duration['m'] = new_minutes
                                    results[current_id]['duration'] = duration

                                # results[current_id]['task'] = results[current_id].get("task", current_task)
                                # results[current_id]['project'] = results[current_id].get("project", current_project)

                                issue: List[str] = results[current_id].get("issue", [])
                                if current_issue not in issue:
                                    issue.append(current_issue)
                                results[current_id]['issue'] = issue

                                description: List[str] = results[current_id].get("description", [])
                                description.append(current_description)
                                results[current_id]['description'] = description

                    for key, value in results.items():
                        if key.startswith(prefix_sum):
                            logging.log(logging.DEBUG, '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
                            logging.log(logging.INFO, f'  [*] {value.get("current_day")}')
                            logging.log(logging.INFO, f'  [*] {value.get("duration").get("h",0)}h {value.get("duration").get("m",0)}m')
                            logging.log(logging.DEBUG, '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
                        else:
                            if value.get("current_day"):
                                logging.log(logging.NOTICE, 'DATE:')
                                logging.log(logging.INFO, f'  [*] {value.get("current_day")}')
                            if value.get('issue'):
                                logging.log(logging.NOTICE, 'ISSUE:')
                                [logging.log(logging.INFO, f'  [*] {issue}') for issue in value.get('issue', [])]
                            if value.get('duration'):
                                logging.log(logging.NOTICE, 'DURATION:')
                                logging.log(logging.INFO, f'  [*] {value.get("duration").get("h",0)}h {value.get("duration").get("m",0)}m')
                            if value.get('description'):
                                logging.log(logging.NOTICE, 'DESCRIPTION:')
                                [logging.log(logging.INFO, f'  - {description}') for description in value.get('description', [])]
                        logging.log(logging.DEBUG, '###################################################')
                else:
                    logging.log(logging.ERROR, res.status_code)

            # print(json.dumps(parsed, indent=4, sort_keys=False))
        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)

    def convert_time_split(self, seconds):
        seconds = seconds % (24 * 3600)
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        return (hour, minutes)
