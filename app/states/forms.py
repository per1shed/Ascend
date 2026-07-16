from aiogram.fsm.state import State, StatesGroup


class SettingsStates(StatesGroup):
    waiting_value = State()
    waiting_slot_name = State()
    waiting_goal = State()


class OnboardingStates(StatesGroup):
    waiting_slot_name = State()
    waiting_goal = State()


class AdminStates(StatesGroup):
    waiting_user_search = State()
