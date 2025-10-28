import enum
import functools

import sqlalchemy
from sqlalchemy import Column
from sqlmodel import SQLModel, Field, Relationship, select, Session

from authentication import KeycloakUser
from database.model.concept.aiod_entry import AIoDEntryORM, EntryStatus


class User(SQLModel, table=True):  # type: ignore [call-arg]
    """A user which is explicitly registered or uploaded an asset."""

    __tablename__ = "user"
    subject_identifier: str = Field(primary_key=True)


@functools.total_ordering
class PermissionType(enum.Enum):
    # Enum instead of StrEnum because we *never* want to do str-comparison.
    # Definition order is important: permissions defined later include earlier ones
    READ: str = "read"
    WRITE: str = "write"
    ADMIN: str = "admin"

    def __lt__(self, other: "PermissionType") -> bool:
        if not isinstance(other, PermissionType):
            return NotImplemented
        # _sort_order_ is definition order: https://github.com/python/cpython/blob/main/Lib/enum.py
        return self._sort_order_ < other._sort_order_  # type: ignore[attr-defined]


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


def _user_has_permission(
    user: KeycloakUser, aiod_entry: AIoDEntryORM, *, at_least: PermissionType
) -> bool:
    return user.is_admin or any(
        permission.user_identifier == user._subject_identifier and permission.type_ >= at_least
        for permission in aiod_entry.permissions
    )


def user_can_read(user: KeycloakUser, aiod_entry) -> bool:
    if aiod_entry.status == EntryStatus.PUBLISHED:
        return True
    return _user_has_permission(user, aiod_entry, at_least=PermissionType.READ)


user_can_write = functools.partial(_user_has_permission, at_least=PermissionType.WRITE)
user_can_administer = functools.partial(_user_has_permission, at_least=PermissionType.ADMIN)


def register_user(kc_user: KeycloakUser, session: Session) -> User:
    query = select(User).where(User.subject_identifier == kc_user._subject_identifier)
    user = session.scalars(query).first()
    if user is None:
        user = User(subject_identifier=kc_user._subject_identifier)
        session.add(user)
    return user


def set_permission(
    user: KeycloakUser, resource: AIoDEntryORM, session: Session, *, type_: PermissionType
):
    key = {
        "user_identifier": user._subject_identifier,
        "aiod_entry_identifier": resource.identifier,
    }
    permission = session.get(Permission, key)
    if permission is None:
        permission = Permission(user_identifier=user._subject_identifier, aiod_entry=resource)
    permission.type_ = type_
    session.add(permission)
