from datetime import datetime, timedelta
import json
import logging
from typing import Any

import bs4 as bs
import httpx

from ..utils.config import settings


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
class ApiLandwehrService:
    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------
    def __init__(self):
        logging.log(logging.DEBUG, "landwehr-api-service is initiated")

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    PRADO_PAGESTATE: str | None = None
    SSID: str | None = None
    format_date_day = "%Y-%m-%d"
    format_date_day_key = "%d.%m.%Y"
    format_date_time = "%H:%M:%S"

    always_worked: dict[str, Any] | None = None

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def upload(self, year: int, month: int, day: int, auftrag: str):
        try:
            with httpx.Client() as session:
                # ------------------------------------------------------------------
                # LOGIN
                res: httpx.Response = self.login(session)

                # ------------------------------------------------------------------
                # LOGIN CHECK
                if (
                    (res.status_code == 200 or res.status_code == 302)
                    and self.PRADO_PAGESTATE is not None
                    and self.SSID is not None
                ):
                    # ----------------------------------------------------------
                    # GET TIME
                    self.get_time(session, year, month)

                    # ----------------------------------------------------------
                    # ADD TIME
                    self.add_time(session, auftrag, year, month, day)

                    # parsed = json.loads(res.text)
                    # logging.log(
                    #     logging.DEBUG,
                    #     json.dumps(parsed, indent=4, sort_keys=False),
                    # )
                else:
                    logging.log(logging.ERROR, res.text)
                    logging.log(logging.ERROR, session.cookies)
                    logging.log(logging.ERROR, res.status_code)
                    # sys.exit(1)
        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def login(self, session: httpx.Client) -> httpx.Response:
        logging.log(logging.INFO, "try to login...")

        # ----------------------------------------------------------------------
        # first make a get, to collect some "hidden fields"

        params = (
            ("page", "Login"),
            ("login", "Personal"),
            ("mandnr", settings.LANDWEHR_MAND_NR),
            ("theme", settings.LANDWEHR_COMPANY),
        )

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,de-DE;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }
        response = httpx.get(
            f"{settings.LANDWEHR_API_URL}{settings.LANDWEHR_API_ENDPOINT}",
            headers=headers,
            params=params,
        )
        self.SSID = response.cookies["SSID"]
        logging.log(logging.DEBUG, self.SSID)

        self.get_prado_pagestate(response.text)

        # ----------------------------------------------------------------------
        # second try to login and save login "hidden fields"

        params = (
            ("page", "Login"),
            ("login", "Personal"),
            ("mandnr", settings.LANDWEHR_MAND_NR),
            ("theme", settings.LANDWEHR_COMPANY),
        )
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,de-DE;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": settings.LANDWEHR_API_URL,
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Referer": f"{settings.LANDWEHR_API_URL}{settings.LANDWEHR_API_ENDPOINT}?page=Login&login=Personal&mandnr={settings.LANDWEHR_MAND_NR}&theme={settings.LANDWEHR_COMPANY}",
            "Sec-Fetch-User": "?1",
        }

        cookies = {
            "SSID": self.SSID,
        }

        data = {
            "PRADO_PAGESTATE": self.PRADO_PAGESTATE,
            "ctl0$PortalLayoutContent$Main$MandantSelect": settings.LANDWEHR_MAND_NR,
            "ctl0$PortalLayoutContent$Main$loginname": settings.LANDWEHR_USERNAME,
            "ctl0$PortalLayoutContent$Main$password": settings.LANDWEHR_PASSWORD,
            "ctl0$PortalLayoutContent$Main$LoginButton": "",
            "PRADO_POSTBACK_TARGET": "ctl0$PortalLayoutContent$Main$LoginButton",
        }

        res = session.post(
            f"{settings.LANDWEHR_API_URL}{settings.LANDWEHR_API_ENDPOINT}",
            headers=headers,
            params=params,
            cookies=cookies,
            data=data,
            follow_redirects=False,
        )
        self.SSID = session.cookies["SSID"]
        logging.log(logging.DEBUG, res.cookies)
        logging.log(logging.DEBUG, session.cookies)
        logging.log(logging.DEBUG, self.SSID)

        return res

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def get_time(self, session: httpx.Client, year: int, month: int) -> httpx.Response | None:
        logging.log(logging.INFO, "try to get current times...")

        # ----------------------------------------------------------------------
        # first try ...

        params = (("page", "Personal.Monatserfassung"),)

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,de-DE;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Referer": f"{settings.LANDWEHR_API_URL}{settings.LANDWEHR_API_ENDPOINT}?page=Login&login=Personal&mandnr={settings.LANDWEHR_MAND_NR}&theme={settings.LANDWEHR_COMPANY}",
        }

        if not self.SSID:
            logging.log(logging.ERROR, "failed because SSID is not set")
            return None

        cookies = {
            "SSID": self.SSID,
        }

        res = session.get(
            f"{settings.LANDWEHR_API_URL}{settings.LANDWEHR_API_ENDPOINT}",
            headers=headers,
            params=params,
            cookies=cookies,
        )
        self.get_prado_pagestate(res.text)

        # ----------------------------------------------------------------------
        # second try ...

        params = (("page", "Personal.Monatserfassung"),)

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,de-DE;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": settings.LANDWEHR_API_URL,
            "DNT": "1",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Referer": f"{settings.LANDWEHR_API_URL}{settings.LANDWEHR_API_ENDPOINT}?page=Personal.Monatserfassung",
        }

        cookies = {
            "SSID": self.SSID,
        }

        data = {
            "MAX_FILE_SIZE": "33554432",
            "PRADO_PAGESTATE": self.PRADO_PAGESTATE,
            "ctl0$PortalLayoutContent$Main$zeitraum": f"{year}|{month}",
            "ctl0$PortalLayoutContent$Main$SignatureImage": "",
            "ctl0$PortalLayoutContent$Main$TimesheetOverlay$TimesheetKunde": "",
            "ctl0$PortalLayoutContent$Main$TimesheetOverlay$PrintWechsel": "0",
            "PRADO_CALLBACK_TARGET": "ctl0$PortalLayoutContent$Main$StartButton",
        }

        res = session.post(
            f"{settings.LANDWEHR_API_URL}{settings.LANDWEHR_API_ENDPOINT}",
            headers=headers,
            params=params,
            cookies=cookies,
            data=data,
        )
        self.get_prado_pagestate(res.text)

        self.html_table_to_json(res.text)
        return res

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def add_time(self, session: httpx.Client, auftrag: str, year: int, month: int, day: int) -> httpx.Response | None:
        logging.log(logging.INFO, "try to add new current times...")

        time_to_set: datetime = datetime(year=year, month=month, day=day)
        time_to_set_str: str = time_to_set.strftime(self.format_date_day_key)

        if self.always_worked is not None and self.always_worked.get(time_to_set_str, None) is None:
            work_time_from_h: int = 8
            work_time_from_m: int = 0
            work_time_from: datetime = datetime(
                year=1970,
                month=2,
                day=1,
                hour=work_time_from_h,
                minute=work_time_from_m,
            )
            work_time_to_h: int = 17
            work_time_to_m: int = 0
            work_time_to: datetime = datetime(year=1970, month=2, day=1, hour=work_time_to_h, minute=work_time_to_m)

            break_time_from_h: int = 12
            break_time_from_m: int = 0
            break_time_from: datetime = datetime(
                year=1970,
                month=2,
                day=1,
                hour=break_time_from_h,
                minute=break_time_from_m,
            )
            break_time_to_h: int = 13
            break_time_to_m: int = 0
            break_time_to: datetime = datetime(year=1970, month=2, day=1, hour=break_time_to_h, minute=break_time_to_m)

            work_time_hours_worked: int = (work_time_to_h - work_time_from_h) - (break_time_to_h - break_time_from_h)
            work_time_days_worked: float = work_time_hours_worked / 8

            PRADO_CALLBACK_PARAMETER = {
                time_to_set_str: [
                    {
                        "arbeit": {
                            "von": {
                                "date": f"1970-02-01T{(work_time_from + timedelta(hours=-1)).strftime(self.format_date_time)}.000Z",
                                "datum": work_time_from.strftime(self.format_date_time),
                            },
                            "bis": {
                                "date": f"1970-02-01T{(work_time_to + timedelta(hours=-1)).strftime(self.format_date_time)}.000Z",
                                "datum": work_time_to.strftime(self.format_date_time),
                            },
                        },
                        "pause": [
                            {
                                "von": {
                                    "date": f"1970-02-01T{(break_time_from + timedelta(hours=-1)).strftime(self.format_date_time)}.000Z",
                                    "datum": break_time_from.strftime(self.format_date_time),
                                },
                                "bis": {
                                    "date": f"1970-02-01T{(break_time_to + timedelta(hours=-1)).strftime(self.format_date_time)}.000Z",
                                    "datum": break_time_to.strftime(self.format_date_time),
                                },
                            }
                        ],
                        "art": "1",
                        "nacht": False,
                        "status": "0",
                        "schicht": None,
                        "leistung": None,
                        "stunden": work_time_hours_worked,
                        "tage": str(work_time_days_worked),
                        "auftrag": auftrag,
                        "projekt": None,
                        "bemerkung": None,
                    }
                ]
            }
            # logging.log(
            #     logging.DEBUG,
            #     json.dumps(PRADO_CALLBACK_PARAMETER, indent=4, sort_keys=False),
            # )

            params = (("page", "Personal.Monatserfassung"),)

            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0",
                "Accept": "*/*",
                "Accept-Language": "en-US,de-DE;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": settings.LANDWEHR_API_URL,
                "DNT": "1",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "Referer": f"{settings.LANDWEHR_API_URL}{settings.LANDWEHR_API_ENDPOINT}?page=Personal.Monatserfassung",
            }

            cookies = {
                "SSID": "SSID",
            }

            data = {
                "MAX_FILE_SIZE": "33554432",
                "PRADO_PAGESTATE": self.PRADO_PAGESTATE,
                "ctl0$PortalLayoutContent$Main$zeitraum": f"{year}|{month}",
                "ctl0$PortalLayoutContent$Main$SignatureImage": "",
                "ctl0$PortalLayoutContent$Main$TimesheetOverlay$TimesheetKunde": "",
                "ctl0$PortalLayoutContent$Main$TimesheetOverlay$PrintWechsel": "0",
                "PRADO_CALLBACK_PARAMETER": json.dumps(PRADO_CALLBACK_PARAMETER),
                "PRADO_CALLBACK_TARGET": "ctl0$PortalLayoutContent$Main$SendData",
            }
            logging.log(
                logging.DEBUG,
                json.dumps(data, indent=4, sort_keys=False),
            )

            res = session.post(
                f"{settings.LANDWEHR_API_URL}{settings.LANDWEHR_API_ENDPOINT}",
                headers=headers,
                params=params,
                cookies=cookies,
                data=data,
            )
            self.get_prado_pagestate(res.text)

            print(res.text)

            return res
        else:
            logging.log(
                logging.INFO,
                "... your defined time-range is always included (or anything else happen)",
            )
        return None

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def get_prado_pagestate(self, text: str | None):
        if text is not None:
            soup = bs.BeautifulSoup(text, "lxml")
            prado_pagestate_id = soup.find("input", attrs={"id": "PRADO_PAGESTATE"})
            if prado_pagestate_id is not None:
                self.PRADO_PAGESTATE = prado_pagestate_id.get("value")
                logging.log(logging.DEBUG, f"PRADO_PAGESTATE:: {self.PRADO_PAGESTATE}")

    def html_table_to_json(self, text: str | None) -> None:
        if text is not None:
            soup = bs.BeautifulSoup(text, "lxml")
            tbl = soup.find("table", attrs={"class", "erfassung"})
            if tbl is not None:
                logging.log(logging.INFO, "try parse table...")

                table_data = {}
                tbl_body = tbl.find("tbody")

                for tr in tbl_body.find_all("tr", recursive=False):
                    val = {}
                    for i, td in enumerate(tr.find_all("td", recursive=False)):
                        attrs: list[str] = td.get_attribute_list("class")
                        if i == 0:
                            val["tag"] = td.find("span").text
                        elif "datum" in attrs:
                            val["date"] = td.text
                        elif "arbeit" in attrs:
                            val["work_start"] = td.find("input", attrs={"class": "von"}).get("value")
                            val["work_end"] = td.find("input", attrs={"class": "bis"}).get("value")
                        elif "pause" in attrs:
                            val["pause_start"] = td.find("input", attrs={"class": "von"}).get("value")
                            val["pause_end"] = td.find("input", attrs={"class": "bis"}).get("value")
                    if val.get("date") is not None and val.get("work_start") is not None:
                        table_data[val.get("date")] = val

                self.always_worked = table_data
                logging.log(logging.DEBUG, json.dumps(table_data, indent=4))
