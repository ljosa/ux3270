"""IBM 3270 standard color definitions.

The IBM 3279 Color Display Station (1979) introduced 7 colors:
- Blue (x'F1'), Red (x'F2'), Pink (x'F3'), Green (x'F4')
- Turquoise (x'F5'), Yellow (x'F6'), White (x'F7')

Standard color conventions in 3270 applications:
- Green: Default text, unprotected input fields
- Blue: Protected fields, labels
- White: Intensified/highlighted text
- Red: Errors
- Turquoise: Informational text
- Yellow: Warnings, attention
- Pink: Special emphasis (rarely used)
"""


class Colors:
    """ANSI escape codes matching IBM 3270 color conventions."""

    # Reset
    RESET = "\033[0m"

    # Standard IBM 3270 colors (using ANSI equivalents)
    BLUE = "\033[34m"
    RED = "\033[31m"
    PINK = "\033[35m"  # Magenta
    GREEN = "\033[32m"
    TURQUOISE = "\033[36m"  # Cyan
    YELLOW = "\033[33m"
    WHITE = "\033[37m"

    # Bright/intensified versions
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_PINK = "\033[95m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_TURQUOISE = "\033[96m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_WHITE = "\033[97m"

    # Text attributes
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    REVERSE = "\033[7m"

    # Semantic colors (IBM 3270 conventions)
    DEFAULT = GREEN  # Standard terminal text
    PROTECTED = TURQUOISE  # Protected/label fields
    INPUT = BRIGHT_GREEN  # Unprotected input fields
    INTENSIFIED = BRIGHT_WHITE  # Highlighted/intensified
    ERROR = BRIGHT_RED  # Error messages
    WARNING = YELLOW  # Warning messages
    INFO = TURQUOISE  # Informational text
    SUCCESS = BRIGHT_GREEN  # Success messages
    TITLE = BRIGHT_WHITE  # Screen titles
    HEADER = BRIGHT_TURQUOISE  # Column headers

    @classmethod
    def protected(cls, text: str) -> str:
        """Format text as protected (label) field."""
        return f"{cls.PROTECTED}{text}{cls.RESET}"

    @classmethod
    def input_field(cls, text: str) -> str:
        """Format text as input field."""
        return f"{cls.INPUT}{text}{cls.RESET}"

    @classmethod
    def intensified(cls, text: str) -> str:
        """Format text as intensified (highlighted)."""
        return f"{cls.INTENSIFIED}{cls.BOLD}{text}{cls.RESET}"

    @classmethod
    def error(cls, text: str) -> str:
        """Format text as error message."""
        return f"{cls.ERROR}{text}{cls.RESET}"

    @classmethod
    def warning(cls, text: str) -> str:
        """Format text as warning message."""
        return f"{cls.WARNING}{text}{cls.RESET}"

    @classmethod
    def info(cls, text: str) -> str:
        """Format text as informational."""
        return f"{cls.INFO}{text}{cls.RESET}"

    @classmethod
    def success(cls, text: str) -> str:
        """Format text as success message."""
        return f"{cls.SUCCESS}{text}{cls.RESET}"

    @classmethod
    def title(cls, text: str) -> str:
        """Format text as screen title."""
        return f"{cls.TITLE}{cls.BOLD}{text}{cls.RESET}"

    @classmethod
    def header(cls, text: str) -> str:
        """Format text as column header."""
        return f"{cls.HEADER}{cls.BOLD}{text}{cls.RESET}"

    @classmethod
    def dim(cls, text: str) -> str:
        """Format text as dimmed (for hints)."""
        return f"{cls.DIM}{text}{cls.RESET}"
