"""Entry point for the Smart Expense Tracker."""
import sys

from database import initialize_database
from cli import build_parser


def main() -> None:
    initialize_database()

    parser = build_parser()
    args = parser.parse_args()

    # GUI mode
    if getattr(args, "gui", False):
        try:
            from gui import launch_gui
            launch_gui()
        except ImportError as exc:
            print(f"GUI unavailable: {exc}")
            sys.exit(1)
        return

    # No subcommand given — print help
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
