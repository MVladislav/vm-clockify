import json
import logging
import sys
from datetime import datetime
from typing import Dict, Optional
from xmlrpc.client import Boolean

import requests
from requests import Session

from ..utils.config import settings
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
    def __init__(self):
        logging.log(logging.DEBUG, 'youtrack-api-service is initiated')

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------
    # https://www.jetbrains.com/help/youtrack/devportal/resource-api-issues-issueID-timeTracking-workItems.html#create-IssueWorkItem-method-sample

    def upload(self, issues: Dict[str, IssueTime]) -> None:
        try:
            format_date_day = '%Y-%m-%d'
            headers = {
                'content-type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {settings.YOUTRACK_API_KEY}',
                'Cache-Control': 'no-cache',
            }
            print(headers)
            with requests.Session() as session:
                for key, issue in issues.items():
                    if not key.startswith('-> sum:') and issue.date is not None:
                        current_day: datetime = datetime.strptime(
                            issue.date, format_date_day
                        )
                        date = int(current_day.strftime('%s')) * 1000
                        description = '\n- '.join(issue.description)
                        description = f'- {description}'
                        body = {
                            'usesMarkdown': True,
                            'date': date,
                            'text': description,
                            'duration': {
                                'presentation': f'{issue.duration.get("h",0)}h {issue.duration.get("m",0)}m'
                            },
                        }
                        if '...' in issue.issue[0]:
                            logging.log(logging.INFO, f'for description ->')
                            logging.log(logging.INFO, issue.description)
                            issue.issue[0] = issue.issue[0].replace(
                                '...',
                                input(
                                    f'==> enter number to replace "..." in {issue.issue[0]}: '
                                ),
                            )
                        if issue.issue_type:
                            issue_type_id = self.get_worktype_id(session, headers, issue.issue[0], issue.issue_type)
                            if issue_type_id:
                                body['type'] = {'id': issue_type_id}

                        is_issue_uploaded = self.check_issue_exists(
                            session, headers, issue.issue[0], description, issue.date, date)
                        if is_issue_uploaded:
                            logging.log(logging.INFO, f"===>> Issue {issue.issue[0]} for date {issue.date} always uploaded")
                        else:
                            path = f'issues/{issue.issue[0]}/timeTracking/workItems'
                            res = session.post(
                                f'{settings.YOUTRACK_API_ENDPOINT}/{settings.YOUTRACK_API_ENDPOINT_SUFFIX}/{path}',
                                headers=headers,
                                json=body,
                            )
                            if res.status_code == 200:
                                parsed = json.loads(res.text)
                                logging.log(
                                    logging.DEBUG,
                                    json.dumps(parsed, indent=4, sort_keys=False),
                                )
                            else:
                                logging.log(logging.ERROR, res.status_code)
                                logging.log(logging.ERROR, res.text)
                                sys.exit(1)
        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)

    def check_issue_exists(self, session: Session, headers, issue_id: str, desc: str, date: str, start_end: int) -> Boolean:
        try:
            start_end = start_end+3600000
            fields = "id,date,text"
            query = f'work: "{desc}" issue: {issue_id} work date: {date}'
            path = f"workItems?fields={fields}&query={query}&author=me&creator=me&start={start_end}&end={start_end}"
            res = session.get(
                f'{settings.YOUTRACK_API_ENDPOINT}/{settings.YOUTRACK_API_ENDPOINT_SUFFIX}/{path}',
                headers=headers
            )
            if res.status_code == 200:
                parsed = json.loads(res.text)
                parsed = next(item for item in parsed if item["text"] == desc and item["date"] == start_end)
                if parsed is not None:
                    return True
        except:
            # will fail when not find anything
            pass
        return False

    def get_worktype_id(self, session: Session, headers, issue_id: str, issue_type: str) -> Optional[str]:
        try:
            projectID = self.get_project_id(session, headers, issue_id)
            if projectID:
                fields = "id,name"
                path = f"admin/projects/{projectID}/timeTrackingSettings/workItemTypes?fields={fields}"
                res = session.get(
                    f'{settings.YOUTRACK_API_ENDPOINT}/{settings.YOUTRACK_API_ENDPOINT_SUFFIX}/{path}',
                    headers=headers
                )
                if res.status_code == 200:
                    parsed = json.loads(res.text)
                    return str(next(item for item in parsed if item["name"] == issue_type)["id"])
        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)
        return None

    def get_project_id(self, session: Session, headers, issue_id: str) -> Optional[str]:
        try:
            if issue_id:
                fields = "id,name"
                path = f"issues/{issue_id}/project?fields={fields}"
                res = session.get(
                    f'{settings.YOUTRACK_API_ENDPOINT}/{settings.YOUTRACK_API_ENDPOINT_SUFFIX}/{path}',
                    headers=headers
                )
                if res.status_code == 200:
                    parsed = json.loads(res.text)
                    return str(parsed["id"])
        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)
        return None
