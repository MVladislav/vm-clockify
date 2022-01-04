import logging
from typing import Dict

from progressbar import ETA, Bar, Counter, ProgressBar, Timer


# ------------------------------------------------------------------------------
#
#
#
# # ------------------------------------------------------------------------------
# class Context:
#     progress: Dict[int, ProgressBar] = {}
#     def __init__(self):
#         logging.log(logging.DEBUG, "init context...")
#         self.service: Any = None
# pass_context = click.make_pass_decorator(Context, ensure=True)
# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
class UtilsProgressHelper:
    progressList: Dict[int, ProgressBar]

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------
    def progress(
        self, id: int, value: int, description: str = "Processing", maxval: int = 100
    ) -> None:
        try:
            if self.progressList.get(id) is None:
                self.progressList[id] = ProgressBar(
                    widgets=[
                        description,
                        " [",
                        Timer(),
                        "] ",
                        Bar(marker="O"),
                        " [",
                        Counter(format="%(value)02d/%(max_value)d"),
                        "]",
                        " (",
                        ETA(),
                        ") ",
                    ],
                    maxval=maxval,
                ).start(
                )
            bar_p: ProgressBar = self.progressList.get(id)
            bar_p.update(value=value)
            if value >= maxval:
                print()
        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)


utilsProgressHelper = UtilsProgressHelper()
