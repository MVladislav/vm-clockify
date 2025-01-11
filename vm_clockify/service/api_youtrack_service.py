"""YOUTRACK."""

from datetime import datetime
import json
import logging
import sys

import httpx

from vm_clockify.utils.config import settings

from .api_clockify_service import IssueTime


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
class ApiYoutrackService:
    """Youtrack service."""

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------
    def __init__(self) -> None:
        """Youtrack service."""
        logging.log(logging.DEBUG, "youtrack-api-service is initiated")
        self.format_date_day: str = "%Y-%m-%d"
        self.headers = {
            "content-type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {settings.YOUTRACK_API_KEY}",
            "Cache-Control": "no-cache",
        }

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------
    # https://www.jetbrains.com/help/youtrack/devportal/resource-api-issues-issueID-timeTracking-workItems.html#create-IssueWorkItem-method-sample

    def upload(self, issues: dict[str, IssueTime]) -> None:
        """Upload to Youtrack."""
        try:
            logging.log(logging.INFO, "Upload to YouTrack started ...")
            with httpx.Client() as session:
                for key, issue in issues.items():
                    if key.startswith("-> sum:") or issue.issue_date is None:
                        continue

                    current_day = int(
                        datetime.strptime(issue.issue_date, self.format_date_day).replace(tzinfo=settings.TIME_ZONE).timestamp()
                        * 1000,
                    )

                    description = "\n- ".join(issue.description)
                    description = f"- {description}"
                    body = {
                        "usesMarkdown": True,
                        "text": description,
                        "date": current_day,
                        "duration": {
                            "presentation": f"{issue.duration.get('h', 0)}h {issue.duration.get('m', 0)}m",
                        },
                    }
                    if "..." in issue.issue[0]:
                        logging.log(logging.INFO, "for description ->")
                        logging.log(logging.INFO, issue.description)
                        issue.issue[0] = issue.issue[0].replace(
                            "...",
                            input(f'==> enter number to replace "..." in {issue.issue[0]}: '),
                        )
                    if issue.issue_type:
                        issue_type_id = self._get_work_type_id(session, issue.issue[0], issue.issue_type)
                        if issue_type_id:
                            body["type"] = {"id": issue_type_id}

                    is_issue_uploaded = self._check_issue_exists(
                        session,
                        issue.issue[0],
                        description,
                        issue.issue_date,
                        current_day,
                    )

                    if is_issue_uploaded:
                        logging.log(
                            logging.INFO,
                            f"===>> Issue {issue.issue[0]} for date {issue.issue_date} is always uploaded",
                        )
                        continue

                    path = f"issues/{issue.issue[0]}/timeTracking/workItems"
                    res = session.post(
                        f"{settings.YOUTRACK_API_ENDPOINT}/{settings.YOUTRACK_API_ENDPOINT_SUFFIX}/{path}",
                        headers=self.headers,
                        json=body,
                    )
                    if res.status_code != 200:
                        logging.log(logging.ERROR, res.status_code)
                        logging.log(logging.ERROR, res.text)
                        sys.exit(1)

                    logging.log(logging.INFO, f"  - Issue {issue.issue[0]} was uploaded, process next ...")

                    parsed = json.loads(res.text)
                    logging.log(
                        logging.DEBUG,
                        json.dumps(parsed, indent=4, sort_keys=False),
                    )
            logging.log(logging.INFO, "... Upload to YouTrack finished!")
        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)

    def _check_issue_exists(self, session: httpx.Client, issue_id: str, desc: str, date: str, start_end: int) -> bool:
        fields = "id,date,text"
        query = f'work: "{desc}" issue: {issue_id} work date: {date}'
        # path = f"workItems?fields={fields}&query={query}&author=me&creator=me&start={start_end}&end={(start_end)}"
        path = f"workItems?fields={fields}&query={query}&author=me&creator=me&start={start_end}"
        res = session.get(
            f"{settings.YOUTRACK_API_ENDPOINT}/{settings.YOUTRACK_API_ENDPOINT_SUFFIX}/{path}",
            headers=self.headers,
        )
        if res.status_code == 200:
            parsed = json.loads(res.text)
            try:
                for item in parsed:
                    logging.log(logging.DEBUG, f"  - compare :: {item['text']} :: {desc}")
                    logging.log(logging.DEBUG, f"  - compare :: {item['date']} :: {start_end}")
                return next(item for item in parsed if item["text"] == desc and item["date"] == start_end) is not None
            except StopIteration:
                return False
        return False

    def _get_work_type_id(self, session: httpx.Client, issue_id: str, issue_type: str) -> str | None:
        project_id = self._get_project_id(session, issue_id)
        if project_id:
            fields = "id,name"
            path = f"admin/projects/{project_id}/timeTrackingSettings/workItemTypes?fields={fields}"
            res = session.get(
                f"{settings.YOUTRACK_API_ENDPOINT}/{settings.YOUTRACK_API_ENDPOINT_SUFFIX}/{path}",
                headers=self.headers,
            )
            if res.status_code == 200:
                parsed = json.loads(res.text)
                try:
                    return str(next(item for item in parsed if item["name"] == issue_type)["id"])
                except StopIteration:
                    return None
        return None

    def _get_project_id(self, session: httpx.Client, issue_id: str) -> str | None:
        if issue_id:
            fields = "id,name"
            path = f"issues/{issue_id}/project?fields={fields}"
            res = session.get(
                f"{settings.YOUTRACK_API_ENDPOINT}/{settings.YOUTRACK_API_ENDPOINT_SUFFIX}/{path}",
                headers=self.headers,
            )
            if res.status_code == 200:
                parsed = json.loads(res.text)
                return str(parsed["id"])
        return None
