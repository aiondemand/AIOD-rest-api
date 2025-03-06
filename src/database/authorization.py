import enum

import sqlalchemy
from sqlalchemy import Column
from sqlmodel import SQLModel, Field, Relationship, select, Session, and_

from authentication import KeycloakUser
from database.model.concept.aiod_entry import AIoDEntryORM
from database.model.concept.concept import AIoDConcept


class User(SQLModel, table=True):  # type: ignore [call-arg]
    """A user which is explicitly registered or uploaded an asset."""

    __tablename__ = "user"
    subject_identifier: str = Field(primary_key=True)


class PermissionType(enum.StrEnum):
    READ = enum.auto()
    WRITE = enum.auto()
    ADMIN = enum.auto()


class Permission(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "permission"
    # ondelete="CASCADE" signifies the Permission will be deleted if the referred row is deleted
    aiod_entry_identifier: int = Field(
        foreign_key="aiod_entry.identifier", primary_key=True, ondelete="CASCADE"
    )
    user_identifier: str = Field(
        foreign_key="user.subject_identifier", primary_key=True, ondelete="CASCADE"
    )
    # - [ ] Add group reference:
    #   - [ ] expand primary key to triplet
    #   - [ ] either group or user needs to be None

    type_: PermissionType = Field(
        sa_column=Column(sqlalchemy.Enum(PermissionType)), default=PermissionType.READ
    )
    aiod_entry: AIoDEntryORM = Relationship(
        back_populates="permissions",
    )


def user_can_read(user: KeycloakUser, aiod_entry) -> bool:
    # TODO:
    #  - [ ] add option for private entries
    #  - [ ] check if any permissions exist (read is least permissive)
    return True


def user_can_write(user: KeycloakUser, aiod_entry) -> bool:
    # TODO: check for write or admin permission
    return False


def register_user(kc_user: KeycloakUser, session: Session) -> User:
    query = select(User).where(User.subject_identifier == kc_user._subject_identifier)
    user = session.scalars(query).first()
    if user is None:
        user = User(subject_identifier=kc_user._subject_identifier)
        session.add(user)
    return user


def add_administrator(user: KeycloakUser, resource: AIoDConcept, session: Session):
    query = select(Permission).where(
        and_(
            Permission.user_identifier == user._subject_identifier,
            Permission.aiod_entry_identifier == resource.aiod_entry_identifier,
        )
    )
    permission = session.scalars(query).first()
    if permission is None:
        permission = Permission(
            user_identifier=user._subject_identifier,
            aiod_entry=resource.aiod_entry,
        )
    permission.type_ = PermissionType.ADMIN
    session.add(permission)


def user_can_administer(user: KeycloakUser, aiod_entry: AIoDEntryORM) -> bool:
    return any(
        permission.user_identifier == user._subject_identifier
        and permission.type_ == PermissionType.ADMIN
        for permission in aiod_entry.permissions
    )
