import json
import logging
import pickle
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Match, Tuple, Union
from urllib.parse import parse_qs

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
        self.project: Union[str, None] = None
        self.task: Union[str, None] = None
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
        logging.log(logging.DEBUG, "clockify-api-service is initiated")

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def user(self) -> None:
        try:
            headers = {
                'content-type': 'application/json',
                'X-Api-Key': settings.CLOCKIFY_API_KEY,
            }
            with requests.Session() as session:
                res = session.get(
                    f"{settings.CLOCKIFY_API_ENDPOINT}/user", headers=headers
                )
                parsed = json.loads(res.text)
                logging.log(logging.INFO, f'USER ID             : {parsed["id"]}')
                logging.log(
                    logging.INFO, f'ACTIVE WORKSPACE    : {parsed["activeWorkspace"]}'
                )
                logging.log(
                    logging.INFO, f'DEFAULT WORKSPACE   : {parsed["defaultWorkspace"]}'
                )
        # logging.log(logging.DEBUG, json.dumps(parsed, indent=4, sort_keys=False))
        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)

    def times(
        self,
        workspaceId: str,
        userId: str,
        days_to_subtract: int = 0,
        page_size: int = 50,
        specific_day: Union[str, None] = None,
        project_name: Union[str, None] = None,
        task_name: Union[str, None] = None,
    ) -> Union[Dict[str, IssueTime], None]:
        try:
            prefix_sum = "-> sum:"
            prefix_duration = "PT"
            # 2021-10-26T13:00:00Z
            format_date_from = "%Y-%m-%dT%H:%M:%SZ"
            format_date_day = "%Y-%m-%d"
            regex_issue = r".*?\[(.*?)\].*?"
            regex_duration = r"PT(?:([0-9]{1,2})H){0,1}(?:([0-9]{1,2})M){0,1}"
            tmp_day: Union[datetime, None] = datetime.now()
            start_day: Union[str, None] = None
            end_day: Union[str, None] = tmp_day.strftime("%Y-%m-%dT23:59:59.000Z") if tmp_day else None
            if specific_day is not None:
                tmp_day = datetime.strptime(specific_day, format_date_day)
                end_day = tmp_day.strftime("%Y-%m-%dT23:59:59.000Z")
            # days_to_subtract = 0
            if tmp_day is not None:
                start_day = (tmp_day - timedelta(days=days_to_subtract)).strftime(
                    "%Y-%m-%dT00:00:00.000Z"
                )
            if start_day is not None:
                logging.log(logging.DEBUG, start_day)
                headers = {
                    'content-type': 'application/json',
                    'X-Api-Key': settings.CLOCKIFY_API_KEY,
                }
                params: Iterable[Tuple[str, Union[str, bytes, int, float, None]]] = [
                    ('hydrated', True),
                    # ('consider-duration-format', True),
                    ('page-size', page_size),
                    ('start', start_day),
                    ('end', end_day),
                    # ('project', project_name),
                    # ('task', task_name)
                ]
                path = f"workspaces/{workspaceId}/user/{userId}/time-entries"
                with requests.Session() as session:
                    res = session.get(
                        f"{settings.CLOCKIFY_API_ENDPOINT}/{path}",
                        headers=headers,
                        params=params,
                    )
                    if res.status_code == 200:
                        parsed = json.loads(res.text)
                        results: Dict[str, IssueTime] = {}
                        if isinstance(parsed, list):
                            for work in parsed:
                                if isinstance(work, dict):
                                    # parse first all needed values from json
                                    timeStart: Union[str, None] = work.get(
                                        "timeInterval", {}
                                    ).get(
                                        "start", None
                                    ) if work.get("timeInterval") is not None else None
                                    timeDuration: Union[str, None] = work.get(
                                        "timeInterval", {}
                                    ).get(
                                        "duration", None
                                    ) if work.get("timeInterval") is not None else None
                                    current_timeDuration = None
                                    if timeDuration and timeDuration.startswith(prefix_duration):
                                        timeDuration_tmp = re.match(
                                            regex_duration, timeDuration
                                        )
                                        if timeDuration_tmp is not None:
                                            current_timeDuration = {
                                                'h': int(
                                                    timeDuration_tmp.group(1)
                                                ) if timeDuration_tmp.group(
                                                    1
                                                ) else 0,
                                                'm': int(
                                                    timeDuration_tmp.group(2)
                                                ) if timeDuration_tmp.group(
                                                    2
                                                ) else 0,
                                            }
                                    current_task: Union[str, None] = work.get(
                                        "task", {}
                                    ).get(
                                        "name", None
                                    ) if work.get("task") is not None else None
                                    current_project: Union[str, None] = work.get(
                                        "project", {}
                                    ).get(
                                        "name", None
                                    ) if work.get("project") is not None else None

                                    # add this or remove
                                    # to combine same issues or split them them
                                    clockify_issue_id: Union[str, None] = work.get(
                                        "id", ""
                                    )

                                    current_description: str = str(
                                        work.get("description")
                                    )
                                    # try to parse the start date into datetime object
                                    current_timeStart: Union[
                                        datetime, None
                                    ] = datetime.strptime(
                                        timeStart, format_date_from
                                    ) if timeStart else None

                                    # filter
                                    if current_project is not None and project_name is not None and project_name not in current_project:
                                        current_project = None
                                    if current_task is not None and task_name is not None and task_name not in current_task:
                                        current_task = None

                                    # if time can be parsed, start to save the result
                                    if current_timeStart is not None and current_task is not None and current_project is not None and current_description is not None and current_timeDuration is not None:
                                        # ----------------------------------------------
                                        # if start date parsed correct, get only current day without time
                                        current_day: str = current_timeStart.strftime(
                                            format_date_day
                                        )
                                        # get needed info like id from issue
                                        current_issue, current_issue_type = self.parse_issue_extra_info(
                                            current_task, current_project, current_description)

                                        if current_issue is not None:
                                            # ----------------------------------------------
                                            # S1:: for a complet time overview for a day
                                            # SETUP:: id to store collections combined unique
                                            self.gen_issue(
                                                results,
                                                current_id=f'{prefix_sum} {current_day}',
                                                current_project=current_project,
                                                current_task=current_task,
                                                current_day=current_day,
                                                current_timeDuration=current_timeDuration,
                                            )
                                            # ----------------------------------------------
                                            # S2:: the issues combined it self
                                            # SETUP:: id to store collections combined unique
                                            self.gen_issue(
                                                results,
                                                current_id=f'{current_day}_{current_project}_{current_task}_{clockify_issue_id}',
                                                current_project=current_project,
                                                current_task=current_task,
                                                current_day=current_day,
                                                current_timeDuration=current_timeDuration,
                                                current_issue=current_issue,
                                                current_issue_type=current_issue_type,
                                                current_description=current_description,
                                            )
                                        # ----------------------------------------------
                                        else:
                                            logging.log(
                                                logging.WARNING,
                                                "failed to get or parse issue number",
                                            )
                                    # ----------------------------------------------
                                    elif (task_name is None and project_name is None):
                                        logging.log(
                                            logging.WARNING,
                                            "failed to get or parse base issue information for:",
                                        )
                                        logging.log(
                                            logging.WARNING,
                                            f"""
    - timeStart: {current_timeStart}
    - task: {current_task}
    - project: {current_project}
    - description: {current_description}
    - timeDuration: {current_timeDuration}
                                            """,
                                        )
                        # add also a generic buffer issue for not specific work
                        if (task_name is None and project_name is None) and settings.WORK_TIME_DEFAULT_ISSUE is not None and settings.WORK_TIME_DEFAULT_COMMENT is not None:
                            for key, value in results.copy().items():
                                if key.startswith(prefix_sum) and value.project is not None and value.task is not None and value.date is not None:
                                    opened_rest_time = settings.WORK_TIME_DEFAULT_HOURS - (
                                        value.duration.get("h", 0) +
                                        (value.duration.get("m", 0) / 60)
                                    )
                                    # only if there is missing time, else no buffer issue is needed
                                    if opened_rest_time > 0:
                                        new_hour, new_minutes = self.convert_time_split(
                                            opened_rest_time * 60.0 * 60.0
                                        )
                                        current_timeDuration = {
                                            'h': new_hour, 'm': new_minutes
                                        }

                                        self.gen_issue(
                                            results,
                                            current_id=f"{settings.WORK_TIME_DEFAULT_ISSUE}_{value.date}_{value.project}_{value.task}",
                                            current_project=value.project,
                                            current_task=value.task,
                                            current_day=value.date,
                                            current_timeDuration=current_timeDuration,
                                            current_issue=settings.WORK_TIME_DEFAULT_ISSUE,
                                            current_description=settings.WORK_TIME_DEFAULT_COMMENT,
                                        )
                        # ------------------------------------------------------
                        # write result to file, to be used later for other api's
                        # example to import it
                        with open(
                            f"{create_service_folder()}/{settings.CLOCKIFY_TMP_FILE}",
                            "wb",
                        ) as f:
                            pickle.dump(results, f)
                        # print the result for manual check or copy/past usage
                        for key, value in results.items():
                            # print a overview for the complete day work
                            if key.startswith(prefix_sum):
                                logging.log(
                                    logging.INFO,
                                    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
                                )
                                logging.log(logging.INFO, f"  ==> DAY: {value.date}")
                                logging.log(
                                    logging.INFO,
                                    f'  [*] WORKED: {value.duration.get("h",0)}h {value.duration.get("m",0)}m',
                                )
                                opened_rest_time = settings.WORK_TIME_DEFAULT_HOURS - (
                                    value.duration.get("h", 0) +
                                    (value.duration.get("m", 0) / 60)
                                )
                                new_hour, new_minutes = self.convert_time_split(
                                    opened_rest_time * 60 * 60
                                )
                                logging.log(
                                    logging.INFO,
                                    f"  [*] REST  : {new_hour}h {new_minutes}m",
                                )
                                logging.log(
                                    logging.INFO,
                                    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
                                )
                            # print issue per issue with information
                            else:
                                # if value.date:
                                #     logging.log(verboselogs.NOTICE, "ID:")
                                #     logging.log(logging.INFO, f"  [*] {key}")
                                if value.date:
                                    logging.log(verboselogs.NOTICE, "DATE:")
                                    logging.log(logging.INFO, f"  [*] {value.date}")
                                if value.issue:
                                    logging.log(verboselogs.NOTICE, "ISSUE:")
                                    for issue in value.issue:
                                        logging.log(logging.INFO, f"  [*] {issue}")
                                if value.issue_type:
                                    logging.log(verboselogs.NOTICE, "I-TYPE:")
                                    logging.log(logging.INFO, f"  [*] {value.issue_type}")
                                if value.duration:
                                    logging.log(verboselogs.NOTICE, "DURATION:")
                                    logging.log(
                                        logging.INFO,
                                        f'  [*] {value.duration.get("h",0)}h {value.duration.get("m",0)}m',
                                    )
                                if value.description:
                                    logging.log(verboselogs.NOTICE, "DESCRIPTION:")
                                    for description in value.description:
                                        logging.log(logging.INFO, f"  - {description}")
                            logging.log(
                                logging.INFO,
                                "###################################################",
                            )
                        return results

                    else:
                        logging.log(logging.ERROR, res.status_code)
                        logging.log(logging.ERROR, res.text)
            # logging.log(logging.DEBUG,json.dumps(parsed, indent=4, sort_keys=False))
            else:
                logging.log(logging.ERROR, "start day can not be created")
        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)
        return None

    def gen_issue(
        self,
        results: Dict[str, IssueTime],
        current_id: str,
        current_project: str,
        current_task: str,
        current_day: str,
        current_timeDuration: Dict[str, int],
        current_issue: Union[str, None] = None,
        current_issue_type: Union[str, None] = None,
        current_description: Union[str, List[Any], None] = None,
    ):
        # START:: insert or update time per day
        # get the issue by ID or create new one into result list
        results[current_id] = results.get(current_id, IssueTime())

        # set project and task infos
        results[current_id].project = current_project
        results[current_id].task = current_task
        results[current_id].date = current_day
        results[current_id].issue_type = current_issue_type

        if current_timeDuration is not None:
            # calc and set the work-time
            duration: Dict[str, int] = results[current_id].duration
            duration["h"] = duration.get("h", 0) + current_timeDuration.get("h", 0)
            duration["m"] = duration.get("m", 0) + current_timeDuration.get("m", 0)
            if duration["m"] >= 60:
                new_hour, new_minutes = self.convert_time_split(duration["m"] * 60)
                duration["h"] = duration.get("h", 0) + new_hour
                duration["m"] = new_minutes

            # add the youtrack issue number
            if isinstance(current_issue, str) and current_issue not in results[
                current_id
            ].issue:
                results[current_id].issue.append(current_issue)
                if len(results[current_id].issue) > 1:
                    logging.log(
                        logging.WARNING,
                        f'issue "{current_description}" has multiple ids, check this',
                    )

            # add description text for issue
            if isinstance(current_description, str):
                results[current_id].description.append(current_description)
            elif isinstance(current_description, list):
                results[current_id].description.extend(current_description)

    def convert_time_split(self, seconds: float) -> Tuple[int, int]:
        seconds = seconds % (24.0 * 3600.0)
        hour = seconds // 3600.0
        seconds %= 3600.0
        minutes = seconds // 60.0
        seconds %= 60.0
        return (int(hour), int(minutes))

    def parse_issue_extra_info(self, current_task: str, current_project: str, current_description: str):
        regex_issue = r'(?:(?:.*?)\[(.*?)\](?:.*?))+$'

        # SETUP:: parse issue number from task or project
        # need to be format: 'example name [i=issue-id]'
        # or                 'example name [i=issue-...]'
        current_issue: Union[
            str, Match[Any], None
        ] = re.match(
            regex_issue, current_task
        ) if current_task else re.match(
            regex_issue, current_project
        )
        if isinstance(current_issue, Match):
            current_issue = current_issue.group(1)
        if current_issue is None:
            logging.log(
                logging.WARNING,
                f'issue "{current_description}" has not id in task or project',
            )

        if isinstance(current_issue, str):
            parsed_result: Dict[Any, Any] = parse_qs(current_issue)

            # get issue ID
            parsed_result_id = parsed_result.get("i")
            if parsed_result_id:
                parsed_result_id = parsed_result_id[0]

            # get issue TYPE
            parsed_result_type = parsed_result.get("t")
            if parsed_result_type:
                parsed_result_type = parsed_result_type[0]

            return parsed_result_id, parsed_result_type

        return None, None
