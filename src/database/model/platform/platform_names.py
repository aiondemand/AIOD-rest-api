import enum


class PlatformName(str, enum.Enum):
    """
    The platforms that are connected to AIoD, and AIoD itself. Every resource is part of a platform.
    To make it possible to add resources from other platforms, the actual platform is stored in
    Platform, a ORM class. On setup, Platform is filled with the values of this enum.
    """

    aiod = "aiod"
    example = "example"
    openml = "openml"
    huggingface = "huggingface"
    zenodo = "zenodo"
    ai4experiments = "ai4experiments"
