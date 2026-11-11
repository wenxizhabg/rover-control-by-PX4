"""US-04/T1: ánh xạ phím bấm thành hành động và tạo bảng hướng dẫn."""

from rover .types import Action


KEY_BINDINGS: list[tuple[str, Action, str]] = [
    ("h", Action .TOGGLE_HELP, "ẩn / hiện hướng dẫn"),
    ("q", Action .QUIT, "thoát app"),
]


def action_for (key: str | None) -> Action | None:
    """Trả hành động tương ứng với phím, không phân biệt chữ hoa hay chữ thường."""
    if key is None:
        return None

    normalized_key = key .lower ()
    for bound_key, action, _description in KEY_BINDINGS:
        if normalized_key == bound_key:
            return action
    return None


def help_lines () -> list[str]:
    """Trả các dòng hướng dẫn theo thứ tự phím được khai báo trong KEY_BINDINGS."""
    return [
        f"{key .upper ()}  {description}"
        for key, _action, description in KEY_BINDINGS
    ]
