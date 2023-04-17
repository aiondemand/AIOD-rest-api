from sqlalchemy import String, UniqueConstraint, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from database.model.ai_resource import OrmAIResource


class OrmCodeArtifact(OrmAIResource):
    """Any code artifact."""

    __tablename__ = "code_artifacts"
    __table_args__ = (
        UniqueConstraint(
            "platform",
            "platform_identifier",
            name="publication_unique_platform_platform_identifier",
        ),
    )
    # Required fields
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    # Recommended fields
    doi: Mapped[str] = mapped_column(String(150), nullable=True, default=None)
    abstarct: Mapped[str] = mapped_column(String(5000), nullable=True, default=None)
    hardware_resources_description: Mapped[str] = mapped_column(
        String(5000), nullable=True, default=None
    )
    os_description: Mapped[str] = mapped_column(String(5000), nullable=True, default=None)
    software_dependecies: Mapped[str] = mapped_column(String(5000), nullable=True, default=None)
    other_dependencies: Mapped[str] = mapped_column(String(5000), nullable=True, default=None)
    compilation_process: Mapped[str] = mapped_column(String(5000), nullable=True, default=None)
    compilation_time_seconds: Mapped[int] = mapped_column(Numeric, nullable=True, default=None)
    deployment_process: Mapped[str] = mapped_column(String(5000), nullable=True, default=None)
    deployment_time_seconds: Mapped[int] = mapped_column(Numeric, nullable=True, default=None)
    experiment_worklow: Mapped[str] = mapped_column(String(5000), nullable=True, default=None)
    experiment_estimation_time_seconds: Mapped[int] = mapped_column(
        Numeric, nullable=True, default=None
    )
    results_description: Mapped[str] = mapped_column(String(5000), nullable=True, default=None)
    publication_results_experiment: Mapped[str] = mapped_column(
        String(5000), nullable=True, default=None
    )
    other_notes: Mapped[str] = mapped_column(String(5000), nullable=True, default=None)
