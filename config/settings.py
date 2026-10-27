import os
from dataclasses import dataclass, field

PASSWORD = os.getenv("TEST_PASSWORD", "Scp@1234")


@dataclass(frozen=True)
class Settings:
    username: str = os.getenv("TEST_USERNAME", "ibp_planner")
    password: str = PASSWORD
    standard_user: tuple = ("std_planner", PASSWORD)
    collab_user: tuple = ("collab_planner", PASSWORD)
    swedish_user: tuple = ("åsa.lind", PASSWORD)
    default_credentials: dict = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "default_credentials", {"username": self.username, "password": self.password})


settings = Settings()
