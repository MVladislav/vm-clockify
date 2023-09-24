import json
import logging
import pickle
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Match, Optional, Tuple, Union
from urllib.parse import parse_qs

import holidays
import httpx
import verboselogs
from httpx._types import HeaderTypes, QueryParamTypes

from ..utils.config import settings
from ..utils.utilsHelper import create_service_folder


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
class IssueTime:
    def __init__(self) -> None:
        self.project: Optional[str] = None
        self.task: Optional[str] = None
        self.date: Optional[str] = None
        self.duration: Dict[str, int] = {}
        self.issue: List[str] = []
        self.description: List[str] = []
        self.issue_type: Optional[str] = None


class ApiClockifyService:
    prefix_sum: str = "-> sum:"
    prefix_duration: str = "PT"
    format_date_from: str = "%Y-%m-%dT%H:%M:%SZ"
    format_date_day: str = "%Y-%m-%d"
    format_date_date_start: str = "%Y-%m-%dT00:00:00.000Z"
    format_date_date_end: str = "%Y-%m-%dT23:59:59.000Z"
    # regex_issue = r".*?\[(.*?)\].*?"
    regex_duration: str = r"PT(?:([0-9]{1,2})H){0,1}(?:([0-9]{1,2})M){0,1}"

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
            if not settings.CLOCKIFY_API_KEY:
                logging.log(logging.ERROR, "failed because CLOCKIFY_API_KEY is not set")
                return

            headers = {
                "content-type": "application/json",
                "X-Api-Key": settings.CLOCKIFY_API_KEY,
            }
            with httpx.Client() as session:
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

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def remaining_monthly_work_time(
        self,
        workspaceId: str,
        userId: str,
        year: int,
        month: int,
        taken_free_days: int = 0,
        illness_days: int = 0
    ) -> None:
        if not settings.CLOCKIFY_API_KEY:
            logging.log(logging.ERROR, "failed because CLOCKIFY_API_KEY is not set")
            return None

        page_size: int = 5000
        first_day = date(year, month, 1).strftime(self.format_date_date_start)
        last_day = (date(year, month + 1, 1) - timedelta(days=1)).strftime(self.format_date_date_end)
        total_worked_time_hours: float = 0

        parsed = self.request_records_from_clockify(workspaceId, userId, first_day, last_day, page_size)

        for work in parsed:
            if not isinstance(work, dict):
                continue
            timeDuration: Optional[str] = (
                work.get("timeInterval", {}).get("duration", None)
                if work.get("timeInterval") is not None
                else None
            )

            if timeDuration and timeDuration.startswith(self.prefix_duration):
                timeDuration_tmp = re.match(self.regex_duration, timeDuration)
                if timeDuration_tmp is not None:
                    c_hours = int(timeDuration_tmp.group(1)) if timeDuration_tmp.group(1) else 0
                    c_minutes = int(timeDuration_tmp.group(2)) if timeDuration_tmp.group(2) else 0
                    total_worked_time_hours = (total_worked_time_hours + (c_hours) + c_minutes/60)

        remaining_hours = self.calculate_remaining_hours(year, month, total_worked_time_hours, free_days=taken_free_days, illness_days=illness_days)
        logging.log(logging.INFO, f"Requested time-range : {first_day} - {last_day}")
        logging.log(logging.INFO, f"Worked hours         : {total_worked_time_hours}")
        logging.log(logging.INFO, f"Remaining hours      : {remaining_hours}")
        logging.log(logging.INFO, f"Remaining days       : {remaining_hours/8}")

    def calculate_remaining_hours(self, year: int, month: int, time_still_worked: float, work_time_hours: int = 8, free_days: int = 0, illness_days: int = 0):
        total_work_days = self.get_total_work_days(year, month)
        total_work_hours = total_work_days * work_time_hours  # Assuming 8 hours worked per day
        holiday_list = self.get_holidays(year)
        holiday_hours = sum([8 for date in holiday_list if date.month == month])

        total_work_hours -= holiday_hours
        total_work_hours -= free_days * 8  # Assuming 8 hours per taken free day
        total_work_hours -= illness_days * 8  # Assuming 8 hours per illness day
        remaining_hours = time_still_worked - total_work_hours  # Assuming 160 hours in a month
        return remaining_hours

    def get_total_work_days(self, year: int, month: int) -> int:
        first_day = date(year, month, 1)
        last_day = date(year, month + 1, 1) - timedelta(days=1)
        total_days = (last_day - first_day).days + 1
        total_work_days = sum(1 for day in range(total_days) if (first_day + timedelta(days=day)).weekday() < 5)
        return total_work_days

    def get_holidays(self, year):
        holiday_list = holidays.country_holidays(country="DE", subdiv="BW", years=year)
        return holiday_list

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def times(
        self,
        workspaceId: str,
        userId: str,
        days_to_subtract: int = 0,
        page_size: int = 50,
        specific_day: Optional[str] = None,
        project_name: Optional[str] = None,
        task_name: Optional[str] = None,
        combine: bool = False,
        buffer: bool = False,
        time_details: bool = False,
        time_count: bool = True,
    ) -> Optional[Dict[str, IssueTime]]:
        try:

            tmp_day: Optional[datetime] = datetime.now()
            start_day: Optional[str] = None
            end_day: Optional[str] = None
            if tmp_day is not None:
                tmp_day.strftime(self.format_date_date_end)

            if specific_day is not None:
                tmp_day = datetime.strptime(specific_day, self.format_date_day)
                end_day = tmp_day.strftime(self.format_date_date_end)
            if end_day is None:
                logging.log(
                    logging.ERROR, "failed to create end_day, can not processed"
                )
                exit(1)
            logging.log(logging.DEBUG, end_day)

            if tmp_day is not None:
                start_day = (tmp_day - timedelta(days=days_to_subtract)).strftime(
                    self.format_date_date_start
                )
            if start_day is None:
                logging.log(
                    logging.ERROR, "failed to create start_day, can not processed"
                )
                exit(1)
            logging.log(logging.DEBUG, start_day)

            parsed = self.request_records_from_clockify(workspaceId, userId, start_day, end_day, page_size)
            if parsed is not None:
                results: Dict[str, IssueTime] = {}

                # proceed the parsed api list into its needed task information
                self.proceed_work_issues(
                    results, parsed, combine, project_name, task_name
                )

                # add also a generic buffer issue for not specific work
                if buffer:
                    self.calc_buffer_issue(task_name, project_name, results)

                # ------------------------------------------------------
                # write result to file, to be used later for other api's
                # example to import it into different service
                with open(
                    f"{create_service_folder()}/{settings.CLOCKIFY_TMP_FILE}",
                    "wb",
                ) as f:
                    pickle.dump(results, f)

                # print the result for manual check or copy/past usage
                self.print_result(results, time_details, time_count)
                # logging.log(logging.DEBUG, json.dumps(parsed, indent=4, sort_keys=False))

                return results
        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)
        return None

    def request_records_from_clockify(self, workspaceId: str, userId: str, start_day: str, end_day: str, page_size: int = 50) -> Any:
        """
            start and end day needs to be in format: "%Y-%m-%dT00:00:00.000Z"
        """
        if not settings.CLOCKIFY_API_KEY:
            logging.log(logging.ERROR, "failed because CLOCKIFY_API_KEY is not set")
            return None

        headers: HeaderTypes = {
            "content-type": "application/json",
            "X-Api-Key": settings.CLOCKIFY_API_KEY,
        }
        params: QueryParamTypes = [
            ("hydrated", True),
            ("page-size", page_size),
            ("start", start_day),
            ("end", end_day),
        ]
        path = f"workspaces/{workspaceId}/user/{userId}/time-entries"
        with httpx.Client() as session:
            res = session.get(
                f"{settings.CLOCKIFY_API_ENDPOINT}/{path}",
                headers=headers,
                params=params,
            )
            if res.status_code != 200:
                logging.log(
                    logging.ERROR,
                    f"api call to get time entries failed with code '{res.status_code}' because of '{res.text}'",
                )
                exit(1)

            parsed: Any = json.loads(res.text)
            if not isinstance(parsed, list):
                logging.log(
                    logging.ERROR,
                    "api result could not be parsed as list, no function implemented for this case",
                )
                exit(1)
            return parsed

    def proceed_work_issues(
        self,
        results: Dict[str, IssueTime],
        parsed: Any,
        combine: bool,
        project_name: Optional[str],
        task_name: Optional[str],
    ) -> None:
        for work in parsed:
            if not isinstance(work, dict):
                continue

            # parse first all needed values from json
            timeStart: Optional[str] = (
                work.get("timeInterval", {}).get("start", None)
                if work.get("timeInterval") is not None
                else None
            )
            timeDuration: Optional[str] = (
                work.get("timeInterval", {}).get("duration", None)
                if work.get("timeInterval") is not None
                else None
            )
            current_timeDuration = None
            if timeDuration and timeDuration.startswith(self.prefix_duration):
                timeDuration_tmp = re.match(self.regex_duration, timeDuration)
                if timeDuration_tmp is not None:
                    current_timeDuration = {
                        "h": int(timeDuration_tmp.group(1))
                        if timeDuration_tmp.group(1)
                        else 0,
                        "m": int(timeDuration_tmp.group(2))
                        if timeDuration_tmp.group(2)
                        else 0,
                    }

            current_task: Optional[str] = (
                work.get("task", {}).get("name", None)
                if work.get("task") is not None
                else None
            )
            current_project: Optional[str] = (
                work.get("project", {}).get("name", None)
                if work.get("project") is not None
                else None
            )

            # if combine is true, same tasks will combine into one
            # else default will not combine tasks
            clockify_issue_id: Optional[str] = None
            if not combine:
                clockify_issue_id = work.get("id", "")

            current_description: str = str(work.get("description"))
            # try to parse the start date into datetime object
            current_timeStart: Optional[datetime] = (
                datetime.strptime(timeStart, self.format_date_from)
                if timeStart
                else None
            )

            # filter
            if (
                current_project is not None
                and project_name is not None
                and project_name not in current_project
            ):
                current_project = None
            if (
                current_task is not None
                and task_name is not None
                and task_name not in current_task
            ):
                current_task = None

            # if time can be parsed, start to save the result
            if current_timeStart is None:
                logging.log(logging.ERROR, "failed to parse current date start")
                exit(1)
            # ----------------------------------------------
            # if start date parsed correct, get only current day without time
            current_day: str = current_timeStart.strftime(self.format_date_day)

            # get needed info like the id from issue
            current_issue, current_issue_type = self.parse_issue_extra_info(
                current_task, current_project
            )

            if current_issue is None:
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
                continue

            if current_task is None:
                logging.log(logging.ERROR, "there is no 'task name' specified")
                exit(1)

            if current_project is None:
                logging.log(logging.ERROR, "there is no 'project name' name specified")
                exit(1)

            # ----------------------------------------------
            # S1:: for a complete time overview for a day
            # SETUP:: id to store collections combined unique by its day
            #         prefix_sum is used to filter it later
            self.gen_issue(
                results,
                current_id=f"{self.prefix_sum}_{current_day}",
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
                current_id=f"{current_day}_{current_project}_{current_task}_{clockify_issue_id}",
                current_project=current_project,
                current_task=current_task,
                current_day=current_day,
                current_timeDuration=current_timeDuration,
                current_issue=current_issue,
                current_issue_type=current_issue_type,
                current_description=current_description,
            )

    def calc_buffer_issue(
        self,
        task_name: Optional[str],
        project_name: Optional[str],
        results: Dict[str, IssueTime],
    ) -> None:
        if (
            (
                task_name is not None or project_name is not None
            )  # TODO: check why this was checked
            or settings.WORK_TIME_DEFAULT_ISSUE is None
            or settings.WORK_TIME_DEFAULT_COMMENT is None
        ):
            return

        for key, value in results.copy().items():
            if (
                not key.startswith(self.prefix_sum)
                or value.project is None
                or value.task is None
                or value.date is None
            ):
                continue

            # calc the rest time
            opened_rest_time: float = settings.WORK_TIME_DEFAULT_HOURS - (
                value.duration.get("h", 0) + (value.duration.get("m", 0) / 60.0)
            )

            # add only if there is missing time, else no buffer issue is needed
            if opened_rest_time <= 0:
                continue

            # calc into correct format
            new_hour, new_minutes = self.convert_time_split(
                opened_rest_time * 60.0 * 60.0
            )
            current_timeDuration: Dict[str, int] = {"h": new_hour, "m": new_minutes}
            # add to issues
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

    def print_result(self, results: Dict[str, IssueTime], time_details: bool, time_count: bool):
        for key, value in results.items():
            # print a overview for the complete day work
            if key.startswith(self.prefix_sum) and time_count:
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
                    value.duration.get("h", 0) + (value.duration.get("m", 0) / 60)
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
                logging.log(
                    logging.INFO,
                    "###################################################",
                )
            # print issue per issue with information
            elif time_details:
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

    def gen_issue(
        self,
        results: Dict[str, IssueTime],
        current_id: str,
        current_task: str,
        current_project: str,
        current_day: str,
        current_timeDuration: Optional[Dict[str, int]],
        current_issue: Optional[str] = None,
        current_issue_type: Optional[str] = None,
        current_description: Optional[Union[str, List[Any], None]] = None,
    ) -> None:
        # START:: insert or update time per day
        # get the issue by ID or create new one into result list
        results[current_id] = results.get(current_id, IssueTime())

        # set project and task infos
        results[current_id].project = current_project
        results[current_id].task = current_task
        results[current_id].date = current_day
        results[current_id].issue_type = current_issue_type

        # calc and set the work-time
        if current_timeDuration is not None:
            duration: Dict[str, int] = results[current_id].duration
            duration["h"] = duration.get("h", 0) + current_timeDuration.get("h", 0)
            duration["m"] = duration.get("m", 0) + current_timeDuration.get("m", 0)
            if duration["m"] >= 60:
                new_hour, new_minutes = self.convert_time_split(duration["m"] * 60)
                duration["h"] = duration.get("h", 0) + new_hour
                duration["m"] = new_minutes
        else:
            logging.log(
                logging.WARNING,
                "no work time was set, check if this was correct or you forget to set your worktime",
            )

        # add the youtrack issue number
        # this is done with a check, if combine mode is activated
        # to verify only unique issue numbers are set in clockify for a task
        # else this should be check what is happen
        if (
            isinstance(current_issue, str)
            and current_issue not in results[current_id].issue
        ):
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

    def parse_issue_extra_info(
        self, current_task: Optional[str], current_project: Optional[str]
    ) -> tuple[Any | None, Any | None] | tuple[None, None]:
        regex_issue = r"(?:(?:.*?)\[(.*?)\](?:.*?))+$"

        # SETUP:: parse issue number from task or project
        # need to be format: 'example name [i=issue-id]'
        # or                 'example name [i=issue-...]'
        current_issue: Union[str, Match[Any], None] = None
        if current_task is not None:
            current_issue = re.match(regex_issue, current_task)
            if isinstance(current_issue, Match):
                current_issue = current_issue.group(1)

        if current_project is not None and current_issue is None:
            current_issue = re.match(regex_issue, current_project)
            if isinstance(current_issue, Match):
                current_issue = current_issue.group(1)

        if current_issue is None:
            logging.log(
                logging.WARNING,
                "issue has not any id in task or project set",
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
