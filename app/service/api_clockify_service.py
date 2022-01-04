import json
import logging
import pickle
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Match, Tuple, Union

import requests
import verboselogs

from ..utils.config import settings
from ..utils.utilsFolderHelper import create_service_folder

# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------


class IssueTime:

    def __init__(self) -> None:
        self.date: Union[str, None] = None
        self.duration: Dict[str, int] = {}
        self.issue: List[str] = []
        self.description: List[str] = []
        self.issue_type: Union[str, None] = None


class ApiClockifyService:

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def __init__(self):
        logging.log(logging.DEBUG, 'clockify-api-service is initiated')

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def user(self) -> None:
        try:
            headers = {
                'content-type': 'application/json',
                'X-Api-Key': settings.CLOCKIFY_API_KEY
            }

            with requests.Session() as session:
                res = session.get(f'{settings.CLOCKIFY_API_ENDPOINT}/user', headers=headers)
                parsed = json.loads(res.text)
                logging.log(logging.INFO, f'USER ID             : {parsed["id"]}')
                logging.log(logging.INFO, f'ACTIVE WORKSPACE    : {parsed["activeWorkspace"]}')
                logging.log(logging.INFO, f'DEFAULT WORKSPACE   : {parsed["defaultWorkspace"]}')

                # logging.log(logging.DEBUG, json.dumps(parsed, indent=4, sort_keys=False))
        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)

    def times(self, workspaceId: str, userId: str,
              days_to_subtract: int = 0, page_size: int = 50,
              specific_day: Union[str, None] = None) -> Union[Dict[str, IssueTime], None]:
        try:
            prefix_sum = '-> sum:'
            prefix_duration = 'PT'
            # 2021-10-26T13:00:00Z
            format_date_from = '%Y-%m-%dT%H:%M:%SZ'
            format_date_day = '%Y-%m-%d'
            regex_issue = r'.*?\[(.*?)\].*?'
            regex_duration = r'PT(?:([0-9]{1,2})H){0,1}(?:([0-9]{1,2})M){0,1}'

            tmp_day: Union[datetime, None] = datetime.now()
            start_day: Union[str, None] = None
            end_day: Union[str, None] = tmp_day.strftime('%Y-%m-%dT23:59:59.000Z')
            if specific_day is not None:
                tmp_day = datetime.strptime(specific_day, format_date_day)
                end_day = tmp_day.strftime('%Y-%m-%dT23:59:59.000Z')
                # days_to_subtract = 0
            if tmp_day is not None:
                start_day = (tmp_day - timedelta(days=days_to_subtract)).strftime('%Y-%m-%dT00:00:00.000Z')
            if start_day is not None:
                logging.log(logging.DEBUG, start_day)

                headers = {
                    'content-type': 'application/json',
                    'X-Api-Key': settings.CLOCKIFY_API_KEY
                }

                params: Iterable[Tuple[str, Union[str, bytes, int, float]]] = [
                    ('hydrated', True),
                    ('consider-duration-format', True),
                    ('page-size', page_size),
                    ('start', start_day),
                    ('end', end_day)
                ]

                path = f'workspaces/{workspaceId}/user/{userId}/time-entries'

                with requests.Session() as session:
                    res = session.get(f'{settings.CLOCKIFY_API_ENDPOINT}/{path}', headers=headers, params=params)

                    if res.status_code == 200:
                        parsed = json.loads(res.text)
                        results: Dict[str, IssueTime] = {}

                        if isinstance(parsed, list):
                            for work in parsed:
                                if isinstance(work, dict):
                                    # parse first all needed values from json
                                    timeStart: str = work.get('timeInterval', {}).get('start')
                                    timeDuration: str = work.get('timeInterval', {}).get('duration')
                                    current_timeDuration = None
                                    if timeDuration.startswith(prefix_duration):
                                        timeDuration_tmp = re.match(regex_duration, timeDuration)
                                        if timeDuration_tmp is not None:
                                            current_timeDuration = {
                                                'h': int(timeDuration_tmp.group(1)) if timeDuration_tmp.group(1) else 0,
                                                'm': int(timeDuration_tmp.group(2)) if timeDuration_tmp.group(2) else 0,
                                            }
                                    current_task: str = work.get('task', {}).get('name') if work.get('task') else None
                                    current_project: str = work.get('project', {})['name']
                                    current_description: str = str(work.get('description'))

                                    # try to parse the start date into datetime object
                                    current_timeStart: Union[datetime, None] = datetime.strptime(
                                        timeStart, format_date_from) if timeStart else None
                                    if current_timeStart is not None:
                                        # if start date parsed correct, get only current day without time
                                        current_day: str = current_timeStart.strftime(format_date_day)

                                        # SETUP:: parse issue number from task or project
                                        # need to be format: 'example name [issue-id]'
                                        # or                 'example name [issue-...]'
                                        current_issue: Union[str, Match[Any], None] = re.match(
                                            regex_issue, current_task) if current_task else re.match(regex_issue, current_project)
                                        if isinstance(current_issue, Match):
                                            current_issue = current_issue.group(1)
                                        if current_issue is None:
                                            logging.log(logging.WARNING,
                                                        f'issue "{current_description}" has not id in task or project')

                                        # ----------------------------------------------
                                        # S1:: for a complet time overview for a day

                                        # SETUP:: id to store collections combined unique
                                        current_id = f'{prefix_sum} {current_day}'
                                        # START:: insert or update time per day
                                        results[current_id] = results.get(current_id, IssueTime())
                                        results[current_id].date = current_id
                                        duration: Dict[str, int]
                                        if current_timeDuration is not None:
                                            duration = results[current_id].duration
                                            duration['h'] = duration.get('h', 0) + current_timeDuration.get('h', 0)
                                            duration['m'] = duration.get('m', 0) + current_timeDuration.get('m', 0)
                                            if duration['m'] >= 60:
                                                new_hour, new_minutes = self.convert_time_split(duration['m']*60)
                                                duration['h'] = duration.get('h', 0) + new_hour
                                                duration['m'] = new_minutes

                                        # ----------------------------------------------
                                        # S2:: the issues combined it self

                                        # SETUP:: id to store collections combined unique
                                        current_id = f'{current_day}_{current_project}_{current_task}'

                                        # START:: insert or update collections
                                        results[current_id] = results.get(current_id, IssueTime())
                                        results[current_id].date = current_day
                                        if current_timeDuration is not None:
                                            duration = results[current_id].duration
                                            duration['h'] = duration.get('h', 0) + current_timeDuration.get('h', 0)
                                            duration['m'] = duration.get('m', 0) + current_timeDuration.get('m', 0)
                                            if duration['m'] >= 60:
                                                new_hour, new_minutes = self.convert_time_split(duration['m']*60)
                                                duration['h'] = duration.get('h', 0) + new_hour
                                                duration['m'] = new_minutes
                                        # results[current_id]['task'] = results[current_id].get("task", current_task)
                                        # results[current_id]['project'] = results[current_id].get("project", current_project)
                                        if isinstance(current_issue, str) and current_issue not in results[current_id].issue:
                                            results[current_id].issue.append(current_issue)
                                            if len(results[current_id].issue) > 1:
                                                logging.log(logging.WARNING,
                                                            f'issue "{current_description}" has multiple ids, check this')
                                        results[current_id].description.append(current_description)
                                    else:
                                        logging.log(logging.WARNING, 'failed to get or parse start date')

                        with open(f'{create_service_folder()}/{settings.CLOCKIFY_TMP_FILE}', 'wb') as f:
                            pickle.dump(results, f)

                        for key, value in results.items():
                            if key.startswith(prefix_sum):
                                logging.log(logging.DEBUG, '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
                                logging.log(logging.INFO, f'  [*] {value.date}')
                                logging.log(
                                    logging.INFO, f'  [*] {value.duration.get("h",0)}h {value.duration.get("m",0)}m')
                                logging.log(logging.DEBUG, '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
                            else:
                                if value.date:
                                    logging.log(verboselogs.NOTICE, 'DATE:')
                                    logging.log(logging.INFO, f'  [*] {value.date}')
                                if value.issue:
                                    logging.log(verboselogs.NOTICE, 'ISSUE:')
                                    for issue in value.issue:
                                        logging.log(logging.INFO, f'  [*] {issue}')
                                if value.duration:
                                    logging.log(verboselogs.NOTICE, 'DURATION:')
                                    logging.log(
                                        logging.INFO, f'  [*] {value.duration.get("h",0)}h {value.duration.get("m",0)}m')
                                if value.description:
                                    logging.log(verboselogs.NOTICE, 'DESCRIPTION:')
                                    for description in value.description:
                                        logging.log(logging.INFO, f'  - {description}')
                            logging.log(logging.DEBUG, '###################################################')
                        return results
                    else:
                        logging.log(logging.ERROR, res.status_code)
                        logging.log(logging.ERROR, res.text)
                # logging.log(logging.DEBUG,json.dumps(parsed, indent=4, sort_keys=False))
            else:
                logging.log(logging.ERROR, 'start day can not be created')
        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)
        return None

    def convert_time_split(self, seconds: int) -> Tuple[int, int]:
        seconds = seconds % (24 * 3600)
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        return (hour, minutes)
