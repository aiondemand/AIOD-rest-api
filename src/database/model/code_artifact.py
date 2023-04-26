from sqlalchemy import Boolean, String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database.model.ai_resource import OrmAIResource


class OrmCodeArtifact(OrmAIResource):
    """Any code artifact."""

    __tablename__ = "code_artifacts"

    identifier: Mapped[int] = mapped_column(
        ForeignKey("ai_resources.identifier"), init=False, primary_key=True
    )

    # Required fields
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    # Recommended fields
    doi: Mapped[str] = mapped_column(String(150), nullable=True, default=None)
    abstract: Mapped[str] = mapped_column(String(5000), nullable=True, default=None)
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

    contentUrl: Mapped[str] = mapped_column(String(250), nullable=True, default=None)
    machineRunnable: Mapped[bool] = mapped_column(Boolean, nullable=True, default=None)
    type: Mapped[str] = mapped_column(String(250), nullable=True, default=None)
    installationScript: Mapped[str] = mapped_column(String(250), nullable=True, default=None)
    runScrpit: Mapped[str] = mapped_column(String(250), nullable=True, default=None)
    output: Mapped[str] = mapped_column(String(650), nullable=True, default=None)

    __mapper_args__ = {
        "polymorphic_identity": "publication",
        "inherit_condition": identifier == OrmAIResource.identifier,
    }
