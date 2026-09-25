class Logger:
    def info(self, message: str) -> None:
        print(f"[info] {message}")

    def warn(self, message: str) -> None:
        print(f"[warn] {message}")

    def error(self, message: str) -> None:
        print(f"[error] {message}")
