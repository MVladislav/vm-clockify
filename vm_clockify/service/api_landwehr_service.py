"""LANDWEHR."""

from datetime import datetime, timedelta
import json
import logging
from typing import Any

import bs4 as bs
import httpx

from vm_clockify.utils.config import settings


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
class ApiLandwehrService:
    """LANDWEHR."""

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------
    def __init__(self) -> None:
        """INIT LANDWEHR."""
        logging.log(logging.DEBUG, "landwehr-api-service is initiated")

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    prado_pagestate: str | None = None
    ssid: str | None = None
    format_date_day = "%Y-%m-%d"
    format_date_day_key = "%d.%m.%Y"
    format_date_time = "%H:%M:%S"

    always_worked: dict[str, Any] | None = None

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def upload(self, year: int, month: int, day: int, auftrag: str) -> None:
        """Upload to Landwehr."""
        try:
            with httpx.Client() as session:
                # ------------------------------------------------------------------
                # LOGIN
                res: httpx.Response = self._login(session)

                # ------------------------------------------------------------------
                # LOGIN CHECK
                if (res.status_code in (200, 302)) and self.prado_pagestate is not None and self.ssid is not None:
                    # ----------------------------------------------------------
                    # GET TIME
                    self._get_time(session, year, month)

                    # ----------------------------------------------------------
                    # ADD TIME
                    self._add_time(session, auftrag, year, month, day)

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

    def _login(self, session: httpx.Client) -> httpx.Response:
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
        self.ssid = response.cookies["SSID"]
        logging.log(logging.DEBUG, self.ssid)

        self._get_prado_pagestate(response.text)

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
            "Origin": settings.LANDWEHR_API_URL or "",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Referer": (
                f"{settings.LANDWEHR_API_URL}{settings.LANDWEHR_API_ENDPOINT}?page=Login&login=Personal&"
                f"mandnr={settings.LANDWEHR_MAND_NR}&theme={settings.LANDWEHR_COMPANY}"
            ),
            "Sec-Fetch-User": "?1",
        }

        cookies = {
            "SSID": self.ssid,
        }

        data = {
            "PRADO_PAGESTATE": self.prado_pagestate,
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
        self.ssid = session.cookies["SSID"]
        logging.log(logging.DEBUG, res.cookies)
        logging.log(logging.DEBUG, session.cookies)
        logging.log(logging.DEBUG, self.ssid)

        return res

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def _get_time(self, session: httpx.Client, year: int, month: int) -> httpx.Response | None:
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
            "Referer": (
                f"{settings.LANDWEHR_API_URL}{settings.LANDWEHR_API_ENDPOINT}?page=Login&login=Personal&"
                f"mandnr={settings.LANDWEHR_MAND_NR}&theme={settings.LANDWEHR_COMPANY}"
            ),
        }

        if not self.ssid:
            logging.log(logging.ERROR, "failed because SSID is not set")
            return None

        cookies = {
            "SSID": self.ssid,
        }

        res = session.get(
            f"{settings.LANDWEHR_API_URL}{settings.LANDWEHR_API_ENDPOINT}",
            headers=headers,
            params=params,
            cookies=cookies,
        )
        self._get_prado_pagestate(res.text)

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
            "Origin": settings.LANDWEHR_API_URL or "",
            "DNT": "1",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Referer": f"{settings.LANDWEHR_API_URL}{settings.LANDWEHR_API_ENDPOINT}?page=Personal.Monatserfassung",
        }

        cookies = {
            "SSID": self.ssid,
        }

        data = {
            "MAX_FILE_SIZE": "33554432",
            "PRADO_PAGESTATE": self.prado_pagestate,
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
        self._get_prado_pagestate(res.text)

        self._html_table_to_json(res.text)
        return res

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def _add_time(self, session: httpx.Client, auftrag: str, year: int, month: int, day: int) -> httpx.Response | None:
        logging.log(logging.INFO, "try to add new current times...")

        time_to_set: datetime = datetime(year=year, month=month, day=day, tzinfo=settings.TIME_ZONE)
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
                tzinfo=settings.TIME_ZONE,
            )
            work_time_to_h: int = 17
            work_time_to_m: int = 0
            work_time_to: datetime = datetime(
                year=1970,
                month=2,
                day=1,
                hour=work_time_to_h,
                minute=work_time_to_m,
                tzinfo=settings.TIME_ZONE,
            )

            break_time_from_h: int = 12
            break_time_from_m: int = 0
            break_time_from: datetime = datetime(
                year=1970,
                month=2,
                day=1,
                hour=break_time_from_h,
                minute=break_time_from_m,
                tzinfo=settings.TIME_ZONE,
            )
            break_time_to_h: int = 13
            break_time_to_m: int = 0
            break_time_to: datetime = datetime(
                year=1970,
                month=2,
                day=1,
                hour=break_time_to_h,
                minute=break_time_to_m,
                tzinfo=settings.TIME_ZONE,
            )

            work_time_hours_worked: int = (work_time_to_h - work_time_from_h) - (break_time_to_h - break_time_from_h)
            work_time_days_worked: float = work_time_hours_worked / 8

            work_from = (work_time_from + timedelta(hours=-1)).strftime(self.format_date_time)
            work_to = (work_time_to + timedelta(hours=-1)).strftime(self.format_date_time)
            break_from = (break_time_from + timedelta(hours=-1)).strftime(self.format_date_time)
            break_to = (break_time_to + timedelta(hours=-1)).strftime(self.format_date_time)

            prado_callback_parameter = {
                time_to_set_str: [
                    {
                        "arbeit": {
                            "von": {
                                "date": f"1970-02-01T{work_from}.000Z",
                                "datum": work_time_from.strftime(self.format_date_time),
                            },
                            "bis": {
                                "date": f"1970-02-01T{work_to}.000Z",
                                "datum": work_time_to.strftime(self.format_date_time),
                            },
                        },
                        "pause": [
                            {
                                "von": {
                                    "date": f"1970-02-01T{break_from}.000Z",
                                    "datum": break_time_from.strftime(self.format_date_time),
                                },
                                "bis": {
                                    "date": f"1970-02-01T{break_to}.000Z",
                                    "datum": break_time_to.strftime(self.format_date_time),
                                },
                            },
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
                    },
                ],
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
                "Origin": settings.LANDWEHR_API_URL or "",
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
                "PRADO_PAGESTATE": self.prado_pagestate,
                "ctl0$PortalLayoutContent$Main$zeitraum": f"{year}|{month}",
                "ctl0$PortalLayoutContent$Main$SignatureImage": "",
                "ctl0$PortalLayoutContent$Main$TimesheetOverlay$TimesheetKunde": "",
                "ctl0$PortalLayoutContent$Main$TimesheetOverlay$PrintWechsel": "0",
                "PRADO_CALLBACK_PARAMETER": json.dumps(prado_callback_parameter),
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
            self._get_prado_pagestate(res.text)

            print(res.text)  # noqa: T201

            return res
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

    def _get_prado_pagestate(self, text: str | None) -> None:
        if text is not None:
            soup = bs.BeautifulSoup(text, "lxml")
            prado_pagestate_id = soup.find("input", attrs={"id": "PRADO_PAGESTATE"})
            if prado_pagestate_id is not None:
                self.prado_pagestate = prado_pagestate_id.get("value")
                logging.log(logging.DEBUG, f"PRADO_PAGESTATE:: {self.prado_pagestate}")

    def _html_table_to_json(self, text: str | None) -> None:
        if text is not None:
            soup = bs.BeautifulSoup(text, "lxml")
            tbl = soup.find("table", attrs={"class", "erfassung"})
            if tbl is not None:
                logging.log(logging.INFO, "try parse table...")

                table_data: dict[str, Any] = {}
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
                    date_key: str | None = val.get("date")
                    if date_key is not None and val.get("work_start") is not None:
                        table_data[date_key] = val

                self.always_worked = table_data
                logging.log(logging.DEBUG, json.dumps(table_data, indent=4))
