class EventType:
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    SURVEY_DETECTED = "survey_detected"
    SURVEY_PREPARED = "survey_prepared"
    SURVEY_SENT = "survey_sent"
    SUMMARY_GENERATED = "summary_generated"
    MOODLE_COURSE_DETECTED = "moodle_course_detected"
    MOODLE_MODULE_DETECTED = "moodle_module_detected"
    MOODLE_SURVEY_DETECTED = "moodle_survey_detected"
    MOODLE_BLOCKED_DETECTED = "moodle_blocked_detected"
    MOODLE_MODULE_UNLOCKED = "moodle_module_unlocked"

    @classmethod
    def values(cls) -> set[str]:
        return {
            value
            for name, value in cls.__dict__.items()
            if name.isupper() and isinstance(value, str)
        }
