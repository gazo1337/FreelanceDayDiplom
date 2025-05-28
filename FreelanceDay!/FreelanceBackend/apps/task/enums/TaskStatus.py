from enum import Enum

TaskStatus = Enum('TaskStatus', [('CREATED', 0), ('IN_PROGRESS', 1), ('ON_END', 2), ('ENDED', 3)])
TaskStatusIn = ["CREATED", "IN_PROGRESS", "ON_END", "ENDED"]