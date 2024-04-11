# ruff: noqa: UP007, D101, E501
"""Defines SQLAlchemy models and tables for database solution"""
from datetime import UTC, datetime
from enum import StrEnum
from typing import Optional, TypeAlias, Union

from sqlalchemy import JSON, CheckConstraint
from sqlalchemy.dialects.postgresql.json import JSONB
from sqlmodel import Column, Field, Relationship, SQLModel, UniqueConstraint

CellAttributes: TypeAlias = Union[
    list[int | float | str | bool | bool],
    str,
    int,
    float,
    bool,
    None,
]

Attributes: TypeAlias = dict[str, Union[int, float, str, "Attributes"]]

JSON_VARIANT = JSONB().with_variant(JSON(), "sqlite")  # type: ignore[no-untyped-call]


def _now() -> datetime:
    return datetime.now(UTC)


class Project(SQLModel, table=True):
    pkey: Optional[int] = Field(default=None, primary_key=True)
    """Primary key (unique identifier) for the project."""
    project_id: str = Field(index=True, unique=True)
    """The name of the project."""
    suffix: str = Field(index=True)
    """Filetype extension of the project's EDA file (gds, gds.gz, or oas)."""
    description: Optional[str]
    """Description of the project."""
    timestamp: datetime = Field(default_factory=_now, index=True)
    """The date and time (UTC) when the project was created."""
    cells: list["Cell"] = Relationship(
        back_populates="project", sa_relationship_kwargs={"cascade": "all, delete"}
    )
    """The cells in this project."""
    wafers: list["Wafer"] = Relationship(
        back_populates="project", sa_relationship_kwargs={"cascade": "all, delete"}
    )
    """Wafers manufactured and uploaded for this project."""


class Cell(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "project_pkey", "cell_id", name="unique_id_and_project_on_cell"
        ),
    )
    pkey: Optional[int] = Field(default=None, primary_key=True)
    """The primary key (unique identifier) for this cell."""
    cell_id: str = Field(index=True)
    """The cell name."""
    attributes: CellAttributes = Field(sa_column=Column(JSON_VARIANT), default={})
    """Attributes associated with this cell, stored as JSON."""
    project_pkey: int = Field(foreign_key="project.pkey")
    """The associated project primary key."""
    project: Project = Relationship(back_populates="cells")
    """The associated project."""
    timestamp: datetime = Field(default_factory=_now, index=True)
    """The date and time (UTC) when this cell was uploaded."""
    devices: list["Device"] = Relationship(
        back_populates="cell",
        sa_relationship_kwargs={
            "cascade": "all, delete",
            "foreign_keys": "Device.cell_pkey",
        },
    )
    """Devices associated with this cell."""


class Device(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "x",
            "y",
            "angle",
            "mirror",
            "parent_cell_pkey",
            "cell_pkey",
            name="unique_coord_cells_on_device",
        ),
        UniqueConstraint("cell_pkey", "device_id", name="unique_device_ids_per_cell"),
        CheckConstraint(
            "parent_cell_pkey <> cell_pkey", name="unique_device_cell_references"
        ),
        CheckConstraint(
            "(parent_cell_pkey IS NULL and x IS NULL and y IS NULL and angle is NULL and mirror is NULL)"
            " OR "
            "(parent_cell_pkey IS NOT NULL and x IS NOT NULL and y IS NOT NULL and angle IS NOT NULL and mirror IS NOT NULL)",
            name="parent_cell_coordinate_reference_not_null",
        ),
    )
    pkey: Optional[int] = Field(default=None, primary_key=True)
    """The primary key (unique identifier) for this device."""
    cell: Cell = Relationship(
        back_populates="devices",
        sa_relationship_kwargs={"foreign_keys": "Device.cell_pkey"},
    )
    """The cell associated with this device."""
    cell_pkey: int = Field(foreign_key="cell.pkey")
    """The primary key of the cell associated with this device."""
    device_id: str = Field(index=True)
    """The name of this device."""
    attributes: dict = Field(sa_column=Column(JSON_VARIANT), default={})  # type: ignore[type-arg]
    """Attributes associated with this device, stored as JSON."""
    x: Optional[float] = Field(default=None, index=True)
    """The x location of the device (its origin), relative to the parent cell."""
    y: Optional[float] = Field(default=None, index=True)
    """The y location of the device (its origin), relative to the parent cell."""
    angle: Optional[float] = Field(default=None, index=True)
    """The angle of rotation of the device, relative to the parent cell."""
    mirror: Optional[bool] = Field(default=None, index=True)
    """True if the device has been mirrored."""
    parent_cell: Optional[Cell] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Device.parent_cell_pkey"}
    )
    """The parent cell and reference frame for the device."""
    parent_cell_pkey: Optional[int] = Field(
        default=None, foreign_key="cell.pkey", nullable=True
    )
    """The parent cell primary key."""
    timestamp: datetime = Field(default_factory=_now, index=True)
    """The date and time (UTC) when the device was uploaded."""
    device_data: list["DeviceData"] = Relationship(
        back_populates="device", sa_relationship_kwargs={"cascade": "all, delete"}
    )
    """Data entries associated with he device."""


class Wafer(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "project_pkey",
            "wafer_id",
            name="unique_wafer_id_per_project",
        ),
    )
    pkey: Optional[int] = Field(default=None, primary_key=True)
    """The primary key (unique identifier) of the wafer."""
    wafer_id: str = Field(index=True)
    """The name of the wafer."""
    description: Optional[str]
    """Description of the wafer."""
    lot_id: Optional[str] = Field(default=None, index=True)
    """The name of the lot which this wafer belongs to (optional)."""
    attributes: dict = Field(sa_column=Column(JSON_VARIANT), default={})  # type: ignore[type-arg]
    """Attributes associated with the wafer, in JSON format."""
    timestamp: datetime = Field(default_factory=_now, index=True)
    """The date and time (UTC) when this wafer was uploaded."""
    project_pkey: int = Field(foreign_key="project.pkey")
    """The primary key of the project associated with this wafer."""
    project: Project = Relationship(back_populates="wafers")
    """The project associated with this wafer."""
    dies: list["Die"] = Relationship(
        back_populates="wafer", sa_relationship_kwargs={"cascade": "all, delete"}
    )
    """Dies in this wafer."""
    analysis: list["Analysis"] = Relationship(
        back_populates="wafer", sa_relationship_kwargs={"cascade": "all, delete"}
    )
    """Wafer-level analyses associated with this wafer."""


class Die(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("x", "y", "wafer_pkey", name="unique_wafer_die"),
    )
    pkey: Optional[int] = Field(default=None, primary_key=True)
    x: int = Field(index=True)
    y: int = Field(index=True)
    die_id: Optional[str] = Field(default=None, index=True)
    attributes: dict = Field(sa_column=Column(JSON_VARIANT), default={})  # type: ignore[type-arg]
    wafer_pkey: int = Field(foreign_key="wafer.pkey")
    wafer: Wafer = Relationship(back_populates="dies")
    timestamp: datetime = Field(default_factory=_now, index=True)
    device_data: list["DeviceData"] = Relationship(
        back_populates="die", sa_relationship_kwargs={"cascade": "all, delete"}
    )
    analysis: list["Analysis"] = Relationship(
        back_populates="die", sa_relationship_kwargs={"cascade": "all, delete"}
    )


class DeviceDataType(StrEnum):
    simulation = "simulation"
    measurement = "measurement"


class DeviceData(SQLModel, table=True):
    __tablename__ = "device_data"
    pkey: Optional[int] = Field(default=None, primary_key=True)
    data_type: DeviceDataType = Field(index=True)
    path: str
    thumbnail_path: Optional[str] = Field(default=None)
    attributes: dict = Field(sa_column=Column(JSON_VARIANT), default={})  # type: ignore[type-arg]
    plotting_kwargs: dict = Field(sa_column=Column(JSON_VARIANT), default_factory=dict)  # type:ignore[type-arg]
    valid: bool = Field(default=True, index=True)
    device: Device = Relationship(back_populates="device_data")
    device_pkey: int = Field(foreign_key="device.pkey", nullable=True)
    die_pkey: Optional[int] = Field(foreign_key="die.pkey", nullable=True)
    die: Optional[Die] = Relationship(back_populates="device_data")
    timestamp: datetime = Field(default_factory=_now, index=True)
    timestamp_acquired: Optional[datetime] = Field(default=None, index=True)
    analysis: list["Analysis"] = Relationship(
        back_populates="device_data", sa_relationship_kwargs={"cascade": "all, delete"}
    )


class AnalysisFunctionTargetModel(StrEnum):
    device_data = "device_data"
    die = "die"
    wafer = "wafer"


class AnalysisFunction(SQLModel, table=True):
    __tablename__ = "analysis_function"
    __table_args__ = (
        UniqueConstraint(
            "analysis_function_id",
            "version",
            name="unique_analysis_function_id_version",
        ),
    )
    pkey: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=_now, index=True)
    analysis_function_id: str = Field(index=True)
    version: int = Field(index=True)
    hash: str = Field(index=True)
    function_path: str
    target_model: AnalysisFunctionTargetModel
    test_target_model_pkey: int
    analysis: list["Analysis"] = Relationship(
        back_populates="analysis_function",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )


class Analysis(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint(
            "1 = (CASE WHEN device_data_pkey IS NOT NULL THEN 1 ELSE 0 END + \
                              CASE WHEN die_pkey IS NOT NULL THEN 1 ELSE 0 END + \
                              CASE WHEN wafer_pkey IS NOT NULL THEN 1 ELSE 0 END)",
            name="analysis_pkeys_xor_constraint",
        ),
    )
    pkey: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=_now, index=True)
    parameters: dict = Field(sa_column=Column(JSON_VARIANT))  # type: ignore[type-arg]
    output: dict = Field(sa_column=Column(JSON_VARIANT))  # type: ignore[type-arg]
    summary_plot: str
    attributes: dict = Field(sa_column=Column(JSON_VARIANT), default={})  # type: ignore[type-arg]
    is_latest: bool = Field(default=True, index=True)
    input_hash: str
    device_data_pkey: Optional[int] = Field(
        foreign_key="device_data.pkey", nullable=True
    )
    device_data: Optional[DeviceData] = Relationship(back_populates="analysis")
    die_pkey: Optional[int] = Field(foreign_key="die.pkey", nullable=True)
    die: Optional[Die] = Relationship(back_populates="analysis")
    wafer_pkey: Optional[int] = Field(foreign_key="wafer.pkey", nullable=True)
    wafer: Optional[Wafer] = Relationship(back_populates="analysis")
    analysis_function_pkey: int = Field(foreign_key="analysis_function.pkey")
    analysis_function: AnalysisFunction = Relationship(
        back_populates="analysis", sa_relationship_kwargs=dict(lazy="joined")
    )

    @property
    def analysis_id(self) -> str:  # noqa
        mapping = {
            "Device Data": self.device_data_pkey,
            "Die": self.die_pkey,
            "Wafer": self.wafer_pkey,
        }
        model_pkey = f"{[ str(k) + ' #' + str(v) for k,v in mapping.items() if v][0] }"
        return f"{self.analysis_function.analysis_function_id} on {model_pkey}"