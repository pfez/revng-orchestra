import logging
from concurrent import futures
from typing import List

from .model.actions.action import Action


class Executor:
    def __init__(self, threads=1, show_output=False):
        self.threads = 1
        self.show_output = show_output
        self._pending_actions = set()
        self._running_actions: List[futures.Future] = []
        self._pool = futures.ThreadPoolExecutor(max_workers=threads, thread_name_prefix="Builder")

    def run(self, action, force=False):
        self._collect_actions(action, force=force)

        for _ in range(self.threads):
            self._schedule_next()

        while self._running_actions:
            done, not_done = futures.wait(self._running_actions, return_when=futures.FIRST_COMPLETED)
            for d in done:
                self._running_actions.remove(d)
                exception = d.exception()
                if exception:
                    logging.critical("An action failed!")
                    if self._pending_actions:
                        logging.critical("Waiting for other running actions to terminate")
                    self._pending_actions = set()
                else:
                    self._schedule_next()

    def _collect_actions(self, action: Action, force=False):
        if not force and action.is_satisfied():
            return

        if action not in self._pending_actions:
            self._pending_actions.add(action)
            for dep in action.dependencies:
                self._collect_actions(dep)

    def _schedule_next(self):
        next_runnable_action = self._get_next_runnable_action()
        if not next_runnable_action:
            if self._pending_actions:
                logging.error(f"Could not run any action! An action has failed or there is a circular dependency")
            return

        future = self._pool.submit(self._run_action, next_runnable_action)
        self._running_actions.append(future)

    def _get_next_runnable_action(self):
        for action in self._pending_actions:
            if all([d.is_satisfied() for d in action.dependencies]):
                self._pending_actions.remove(action)
                return action

    def _run_action(self, action: Action):
        return action.run(show_output=self.show_output)
