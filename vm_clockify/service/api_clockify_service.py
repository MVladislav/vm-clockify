"""CLOCKIFY."""

from datetime import date, datetime, timedelta
import json
import logging
from pathlib import Path
import re
from re import Match
import sys
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs

import holidays
import httpx
import verboselogs

from vm_clockify.utils.config import settings
from vm_clockify.utils.utils_helper import create_service_folder

if TYPE_CHECKING:
    from httpx._types import HeaderTypes, QueryParamTypes


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
class IssueTime:
    """Issue Time."""

    def __init__(
        self,
        project: str | None = None,
        task: str | None = None,
        issue_date: str | None = None,
        duration: dict[str, int] | None = None,
        issue: list[str] | None = None,
        description: list[str] | None = None,
        issue_type: str | None = None,
    ) -> None:
        """Init."""
        if duration is None:
            duration = {}
        if issue is None:
            issue = []
        if description is None:
            description = []
        self.project = project
        self.task = task
        self.issue_date = issue_date
        self.duration = duration
        self.issue = issue
        self.description = description
        self.issue_type = issue_type

    def to_dict(self) -> dict[str, Any]:
        """Convert the dataclass to a dictionary."""
        return dict(self.__dict__.items())


class PrintValues:
    """Print Values."""

    def __init__(
        self,
        issue_date: str | None = None,
        issue: str | None = None,
        issue_type: str | None = None,
        duration: dict[str, int] | None = None,
        description: str | None = None,
    ) -> None:
        """Init."""
        self.date = issue_date
        self.duration = duration
        self.issue = issue
        self.issue_type = issue_type
        self.description = description


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------


class ApiClockifyService:
    """Clockify Service."""

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
    def __init__(self) -> None:
        """Clockify Service."""
        logging.log(logging.DEBUG, "clockify-api-service is initiated")

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def user(self) -> None:
        """Clockify get user info."""
        try:
            if not settings.CLOCKIFY_API_KEY:
                logging.log(logging.ERROR, "failed because CLOCKIFY_API_KEY is not set")
                return

            headers = {
                "content-type": "application/json",
                "X-Api-Key": settings.CLOCKIFY_API_KEY,
            }
            with httpx.Client() as session:
                res = session.get(f"{settings.CLOCKIFY_API_ENDPOINT}/user", headers=headers)
                parsed = json.loads(res.text)
                logging.log(logging.INFO, f"USER ID             : {parsed['id']}")
                logging.log(logging.INFO, f"ACTIVE WORKSPACE    : {parsed['activeWorkspace']}")
                logging.log(logging.INFO, f"DEFAULT WORKSPACE   : {parsed['defaultWorkspace']}")
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
        workspace_id: str,
        user_id: str,
        year: int,
        month: int,
        taken_free_days: int = 0,
        illness_days: int = 0,
    ) -> None:
        """Clockify remaining month work time calc."""
        if not settings.CLOCKIFY_API_KEY:
            logging.log(logging.ERROR, "failed because CLOCKIFY_API_KEY is not set")
            return

        page_size: int = 5000
        first_day = date(year, month, 1).strftime(self.format_date_date_start)
        last_day = (date(year, month + 1, 1) - timedelta(days=1)).strftime(self.format_date_date_end)
        total_worked_time_hours: float = 0

        parsed = self.request_records_from_clockify(workspace_id, user_id, first_day, last_day, page_size)

        if parsed is None:
            logging.log(logging.ERROR, "failed because records not parsed, see error before")
            return

        for work in parsed:
            if not isinstance(work, dict):
                continue
            time_duration: str | None = (
                work.get("timeInterval", {}).get("duration", None) if work.get("timeInterval") is not None else None
            )

            if time_duration and time_duration.startswith(self.prefix_duration):
                time_duration_tmp = re.match(self.regex_duration, time_duration)
                if time_duration_tmp is not None:
                    c_hours = int(time_duration_tmp.group(1)) if time_duration_tmp.group(1) else 0
                    c_minutes = int(time_duration_tmp.group(2)) if time_duration_tmp.group(2) else 0
                    total_worked_time_hours = total_worked_time_hours + (c_hours) + c_minutes / 60

        remaining_hours = self._calculate_remaining_hours(
            year,
            month,
            total_worked_time_hours,
            free_days=taken_free_days,
            illness_days=illness_days,
        )
        logging.log(logging.INFO, f"Requested time-range : {first_day} - {last_day}")
        logging.log(logging.INFO, f"Worked hours         : {total_worked_time_hours}")
        logging.log(logging.INFO, f"Remaining hours      : {remaining_hours}")
        logging.log(logging.INFO, f"Remaining days       : {remaining_hours / 8}")

    def _calculate_remaining_hours(
        self,
        year: int,
        month: int,
        time_still_worked: float,
        work_time_hours: int = 8,
        free_days: int = 0,
        illness_days: int = 0,
    ) -> float:
        total_work_days = self._get_total_work_days(year, month)
        total_work_hours = total_work_days * work_time_hours  # Assuming 8 hours worked per day
        holiday_list = self._get_holidays(year)
        holiday_hours = sum(8 for date in holiday_list if date.month == month)

        total_work_hours -= holiday_hours
        total_work_hours -= free_days * 8  # Assuming 8 hours per taken free day
        total_work_hours -= illness_days * 8  # Assuming 8 hours per illness day
        return time_still_worked - total_work_hours  # Assuming 160 hours in a month

    def _get_total_work_days(self, year: int, month: int) -> int:
        first_day = date(year, month, 1)
        last_day = date(year, month + 1, 1) - timedelta(days=1)
        total_days = (last_day - first_day).days + 1
        return sum(1 for day in range(total_days) if (first_day + timedelta(days=day)).weekday() < 5)

    def _get_holidays(self, year: int) -> holidays.HolidayBase:
        return holidays.country_holidays(country="DE", subdiv="BW", years=year)

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def times(
        self,
        workspace_id: str,
        user_id: str,
        days_to_subtract: int = 0,
        page_size: int = 50,
        specific_day: str | None = None,
        filter_project_name: str | None = None,
        filter_task_name: str | None = None,
        filter_issue_id: str | None = None,
        combine: bool = False,
        buffer: bool = False,
        time_details: bool = False,
        time_count: bool = True,
    ) -> dict[str, IssueTime] | None:
        """Clockify generate list of work time."""
        try:
            tmp_day: datetime = datetime.now(tz=settings.TIME_ZONE)
            start_day: str | None = None
            end_day: str = tmp_day.strftime(self.format_date_date_end)

            # if a speicif day should be used as start day, parse it from param
            if specific_day is not None:
                tmp_day = datetime.strptime(specific_day, self.format_date_day).replace(tzinfo=settings.TIME_ZONE)
                end_day = tmp_day.strftime(self.format_date_date_end)
            # calculate start day
            start_day = (tmp_day - timedelta(days=days_to_subtract)).strftime(self.format_date_date_start)

            logging.debug(start_day)
            logging.debug(end_day)

            parsed = self.request_records_from_clockify(workspace_id, user_id, start_day, end_day, page_size)
            if parsed is None:
                return None

            results: dict[str, IssueTime] = {}

            # proceed the parsed api list into its needed task information
            self._proceed_work_issues(results, parsed, combine, filter_project_name, filter_task_name, filter_issue_id)

            # add also a generic buffer issue for not specific work
            if buffer:
                self._calc_buffer_issue(results)

            # ------------------------------------------------------
            # write result to file, to be used later for other api's example to import it into different service
            serializable_results = {
                key: value.to_dict() if isinstance(value, IssueTime) else value for key, value in results.items()
            }
            with Path(f"{create_service_folder()}/{settings.CLOCKIFY_TMP_FILE}").open(mode="w", encoding="utf-8") as f:
                json.dump(serializable_results, f)

            # print the result for manual check or copy/past usage
            self._print_result(results, time_details, time_count)

            return results
        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)
        return None

    def request_records_from_clockify(
        self,
        workspace_id: str,
        user_id: str,
        start_day: str,
        end_day: str,
        page_size: int = 50,
    ) -> list[Any] | None:
        """Start and end day needs to be in format: "%Y-%m-%dT00:00:00.000Z"."""
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
        path = f"workspaces/{workspace_id}/user/{user_id}/time-entries"
        with httpx.Client() as session:
            res = session.get(
                f"{settings.CLOCKIFY_API_ENDPOINT}/{path}",
                headers=headers,
                params=params,
            )
            if res.status_code != 200:
                logging.error(f"api call to get time entries failed with code '{res.status_code}' because of '{res.text}'")
                sys.exit(1)

            parsed: Any = json.loads(res.text)
            if not isinstance(parsed, list):
                logging.error("api result could not be parsed as list, no function implemented for this case")
                sys.exit(1)
            return parsed

    def _proceed_work_issues(
        self,
        results: dict[str, IssueTime],
        parsed: list[Any],
        combine: bool,
        filter_project_name: str | None,
        filter_task_name: str | None,
        filter_issue_id: str | None,
    ) -> None:
        for work in parsed:
            if not isinstance(work, dict):
                continue

            # parse first all needed values from json
            time_start: str | None = (
                work.get("timeInterval", {}).get("start", None) if work.get("timeInterval") is not None else None
            )
            time_duration: str | None = (
                work.get("timeInterval", {}).get("duration", None) if work.get("timeInterval") is not None else None
            )
            current_time_duration = None
            if time_duration and time_duration.startswith(self.prefix_duration):
                time_duration_tmp = re.match(self.regex_duration, time_duration)
                if time_duration_tmp is not None:
                    current_time_duration = {
                        "h": int(time_duration_tmp.group(1)) if time_duration_tmp.group(1) else 0,
                        "m": int(time_duration_tmp.group(2)) if time_duration_tmp.group(2) else 0,
                    }

            current_task: str | None = work.get("task", {}).get("name", None) if work.get("task") is not None else None
            current_project: str | None = work.get("project", {}).get("name", None) if work.get("project") is not None else None

            # if combine is true, same tasks will combine into one
            # else default will not combine tasks
            clockify_issue_id: str | None = None
            if not combine:
                clockify_issue_id = work.get("id", "")

            original_description: str = str(work.get("description"))
            # try to parse the start date into datetime object
            current_time_start: datetime | None = (
                datetime.strptime(time_start, self.format_date_from).replace(tzinfo=settings.TIME_ZONE) if time_start else None
            )

            # filter inside task and project
            if current_project is not None and filter_project_name is not None and filter_project_name not in current_project:
                current_project = None
            if current_task is not None and filter_task_name is not None and filter_task_name not in current_task:
                current_task = None

            # if current_task is None:
            #     logging.debug("there is no 'task name' specified")
            #     continue
            if current_project is None:
                logging.debug("there is no 'project name' name specified")
                continue

            # if time can be parsed, start to save the result
            if current_time_start is None:
                logging.error("failed to parse current date start")
                sys.exit(1)
            # ----------------------------------------------
            # if start date parsed correct, get only current day without time
            current_day: str = current_time_start.strftime(self.format_date_day)

            # get needed info like the id from issue
            current_issue, current_issue_type, current_description = self._parse_issue_extra_info(
                current_task,
                current_project,
                original_description,
            )

            if current_issue is None:
                logging.warning("failed to get or parse base issue information for:")
                logging.warning(
                    f"""
                        - timeStart: {current_time_start}
                        - task: {current_task}
                        - project: {current_project}
                        - description: {current_description}
                        - timeDuration: {current_time_duration}
                    """,
                )

            # filter specific issue
            if filter_issue_id is not None and current_issue is not None and filter_issue_id not in current_issue:
                current_issue = None

            if current_issue is None:
                continue

            # ----------------------------------------------
            # S1:: for a complete time overview for a day
            # SETUP:: id to store collections combined unique by its day
            #         prefix_sum is used to filter it later
            self._gen_issue(
                results,
                current_id=f"{self.prefix_sum}_{current_day}",
                current_project=current_project,
                current_task=current_task,
                current_day=current_day,
                current_time_duration=current_time_duration,
            )
            # ----------------------------------------------
            # S2:: the issues combined it self
            # SETUP:: id to store collections combined unique
            self._gen_issue(
                results,
                current_id=f"{current_day}_{current_project}_{current_task}_{clockify_issue_id}",
                current_project=current_project,
                current_task=current_task,
                current_day=current_day,
                current_time_duration=current_time_duration,
                current_issue=current_issue,
                current_issue_type=current_issue_type,
                current_description=current_description,
            )

    def _calc_buffer_issue(self, results: dict[str, IssueTime]) -> None:
        if settings.WORK_TIME_DEFAULT_ISSUE is None or settings.WORK_TIME_DEFAULT_COMMENT is None:
            return

        for key, value in results.copy().items():
            if not key.startswith(self.prefix_sum) or value.project is None or value.task is None or value.issue_date is None:
                continue

            # calc the rest time
            opened_rest_time: float = settings.WORK_TIME_DEFAULT_HOURS - (
                value.duration.get("h", 0) + (value.duration.get("m", 0) / 60.0)
            )

            # add only if there is missing time, else no buffer issue is needed
            if opened_rest_time <= 0:
                continue

            # calc into correct format
            new_hour, new_minutes = self._convert_time_split(opened_rest_time * 60.0 * 60.0)
            current_time_duration: dict[str, int] = {"h": new_hour, "m": new_minutes}
            # add to issues
            self._gen_issue(
                results,
                current_id=f"{settings.WORK_TIME_DEFAULT_ISSUE}_{value.issue_date}_{value.project}_{value.task}",
                current_project=value.project,
                current_task=value.task,
                current_day=value.issue_date,
                current_time_duration=current_time_duration,
                current_issue=settings.WORK_TIME_DEFAULT_ISSUE,
                current_description=settings.WORK_TIME_DEFAULT_COMMENT,
            )

    def _print_result(self, results: dict[str, IssueTime], time_details: bool, time_count: bool) -> None:
        print_style: int = 0  # 0 | 1

        for key, value in results.items():
            log_parts = []

            # print a overview for the complete day work
            if key.startswith(self.prefix_sum) and time_count:
                logging.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                logging.info(f"  ==> DAY: {value.issue_date}")
                logging.info(f"  [*] WORKED: {value.duration.get('h', 0)}h {value.duration.get('m', 0)}m")
                opened_rest_time = settings.WORK_TIME_DEFAULT_HOURS - (
                    value.duration.get("h", 0) + (value.duration.get("m", 0) / 60)
                )
                new_hour, new_minutes = self._convert_time_split(opened_rest_time * 60 * 60)
                logging.info(f"  [*] REST  : {new_hour}h {new_minutes}m")
                logging.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                # logging.info("###################################################")
            # print issue per issue with information
            elif time_details:
                if print_style == 0:
                    if value.issue_date:
                        log_parts.append(f"{value.issue_date}")
                    if value.duration:
                        log_parts.append(f"{value.duration.get('h', 0)}h {value.duration.get('m', 0)}m")
                    if value.issue:
                        log_parts.append(", ".join(value.issue))
                    if value.issue_type:
                        log_parts.append(value.issue_type)
                    if value.description:
                        log_parts.append(", ".join(value.description))
                    logging.info(f"  [*] {' || '.join(log_parts)}")
                elif print_style == 1:
                    if value.issue_date:
                        self._log_detail("DATE:", f"  [*] {value.issue_date}")
                    if value.duration:
                        self._log_detail("DURATION:", f"  [*] {value.duration.get('h', 0)}h {value.duration.get('m', 0)}m")
                    if value.issue:
                        self._log_detail("ISSUE:", *(f"  [*] {issue}" for issue in value.issue))
                    if value.issue_type:
                        self._log_detail("I-TYPE:", f"  [*] {value.issue_type}")
                    if value.description:
                        self._log_detail("DESCRIPTION:", *(f"  - {desc}" for desc in value.description))
                    logging.info("###################################################")

    def _log_detail(self, header: str, *messages: str) -> None:
        logging.log(verboselogs.NOTICE, header)
        for message in messages:
            logging.info(message)

    def _gen_issue(
        self,
        results: dict[str, IssueTime],
        current_id: str,
        current_task: str | None,
        current_project: str,
        current_day: str,
        current_time_duration: dict[str, int] | None,
        current_issue: str | None = None,
        current_issue_type: str | None = None,
        current_description: str | list[Any] | None = None,
    ) -> None:
        # START:: insert or update time per day
        # get the issue by ID or create new one into result list
        results[current_id] = results.get(current_id, IssueTime())

        # set project and task infos
        results[current_id].project = current_project
        results[current_id].task = current_task
        results[current_id].issue_date = current_day
        results[current_id].issue_type = current_issue_type

        # calc and set the work-time
        if current_time_duration is not None:
            duration: dict[str, int] = results[current_id].duration
            duration["h"] = duration.get("h", 0) + current_time_duration.get("h", 0)
            duration["m"] = duration.get("m", 0) + current_time_duration.get("m", 0)
            if duration["m"] >= 60:
                new_hour, new_minutes = self._convert_time_split(duration["m"] * 60)
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
        if isinstance(current_issue, str) and current_issue not in results[current_id].issue:
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

    def _convert_time_split(self, seconds: float) -> tuple[int, int]:
        seconds = seconds % (24.0 * 3600.0)
        hour = seconds // 3600.0
        seconds %= 3600.0
        minutes = seconds // 60.0
        seconds %= 60.0
        return (int(hour), int(minutes))

    def _parse_issue_extra_info(
        self,
        current_task: str | None,
        current_project: str | None,
        current_description: str | None,
    ) -> tuple[Any | None, Any | None, Any | None]:
        regex_issue = r"(?:(?:.*?)\[(.*?)\](?:.*?))+$"

        # SETUP:: parse issue number from task or project
        # need to be format: 'example name [i=issue-id]'
        # or                 'example name [i=issue-...]'
        current_issue: str | None = None
        if current_description is not None:
            current_issue_tmp = re.match(regex_issue, current_description)
            if isinstance(current_issue_tmp, Match):
                current_issue = current_issue_tmp.group(1)
                # current_description = current_description
                current_description = re.sub(r"\[.*?\]$", "", current_description).strip()

        if current_task is not None:
            current_issue_tmp = re.match(regex_issue, current_task)
            if isinstance(current_issue_tmp, Match):
                current_issue = current_issue_tmp.group(1)

        if current_project is not None:
            current_issue_tmp = re.match(regex_issue, current_project)
            if isinstance(current_issue_tmp, Match):
                current_issue = current_issue_tmp.group(1)

        if current_issue is None:
            logging.log(
                logging.WARNING,
                f"issue has not any id in task or project set {current_issue}",
            )

        if isinstance(current_issue, str):
            parsed_result: dict[Any, Any] = parse_qs(current_issue)

            # get issue ID
            parsed_result_id = parsed_result.get("i")
            if parsed_result_id:
                parsed_result_id = parsed_result_id[0]

            # get issue TYPE
            parsed_result_type = parsed_result.get("t")
            if parsed_result_type:
                parsed_result_type = parsed_result_type[0]

            return parsed_result_id, parsed_result_type, current_description

        return None, None, None
