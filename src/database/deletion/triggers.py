"""
Deletion triggers, to automatically delete rows from related tables.

Note that normally adding cascading deletes is preferable, but that's not always easy because
tables are referenced by multiple tables. See src/README.md for additional information.
"""

from typing import Type

from sqlalchemy import DDL, event
from sqlmodel import SQLModel

from database.model.helper_functions import get_relationships, non_abstract_subclasses


def add_delete_triggers(parent_class: Type[SQLModel]):
    classes: list[Type[SQLModel]] = non_abstract_subclasses(parent_class)
    for cls in classes:
        for name, value in get_relationships(cls).items():
            value.create_triggers(cls, name)


def create_deletion_trigger_one_to_one(
    trigger: Type[SQLModel],
    to_delete: Type[SQLModel],
    trigger_identifier_link: str = "identifier",
    to_delete_identifier: str = "identifier",
):
    """
    Create a trigger for a one-to-one relationship, so that if a row from trigger is deleted, any
    row in the to_delete is also deleted where trigger.trigger_identifier_link ==
    to_delete.to_delete_identifier.

    e.g.
    - trigger: Dataset
    - trigger_identifier_link: "ai_asset_identifier"
    - to_delete: AIAssetTable
    - to_delete_identifier: "identifier"

    Then, after deleting a Dataset, the corresponding AIAsset will also be deleted.

    Args:
        trigger: The table that triggers a deletion
        to_delete: The related table
        trigger_identifier_link: the identifier on the trigger table, that has a foreign key
            relationship to the to_delete_identifier
        to_delete_identifier: the identifier on the related table that is referenced.
    """
    trigger_name = trigger.__tablename__
    delete_name = to_delete.__tablename__

    ddl = DDL(
        f"""
        CREATE TRIGGER delete_{trigger_name}_{delete_name}
        AFTER DELETE ON {trigger_name}
        FOR EACH ROW
        BEGIN
            DELETE FROM {delete_name}
            WHERE {delete_name}.{to_delete_identifier} = OLD.{trigger_identifier_link};
        END;
        """
    )
    event.listen(trigger.metadata, "after_create", ddl)


def create_deletion_trigger_many_to_one(
    trigger: Type[SQLModel],
    to_delete: Type[SQLModel],
    trigger_identifier_link: str,
    to_delete_identifier: str = "identifier",
):
    """
    Create a trigger for a many-to-one relationship, so that if a row from trigger is deleted,
    any **orphan** row in the to_delete is also deleted where trigger.trigger_identifier_link ==
    to_delete.to_delete_identifier.

    Args:
        trigger: The table that triggers a deletion
        to_delete: The related table
        trigger_identifier_link: the identifier on the trigger table, that has a foreign key
            relationship to the to_delete_identifier
        to_delete_identifier: the identifier on the related table that is referenced.
    """
    trigger_name = trigger.__tablename__
    delete_name = to_delete.__tablename__

    ddl = DDL(
        f"""
        CREATE TRIGGER delete_{trigger_name}_{delete_name}
        AFTER DELETE ON {trigger_name}
        FOR EACH ROW
        BEGIN
            DELETE FROM {delete_name}
            WHERE {delete_name}.{to_delete_identifier} = OLD.{trigger_identifier_link}
            AND NOT EXISTS (
                SELECT 1 FROM {trigger_name}
                WHERE {trigger_name}.{trigger_identifier_link} = OLD.{trigger_identifier_link}
            );
        END;
        """
    )
    event.listen(trigger.metadata, "after_create", ddl)


def create_deletion_trigger_many_to_many(
    trigger: Type[SQLModel],
    link: Type[SQLModel],
    to_delete: Type[SQLModel],
    trigger_identifier: str = "identifier",
    link_from_identifier: str = "from_identifier",
    link_to_identifier: str = "linked_identifier",
    to_delete_identifier: str = "identifier",
    other_links: None | list[str] = None,
):
    """
    Create a trigger for a many-to-many relationship, so that if a row from trigger is deleted,
    any **orphan** row in the to_delete is also deleted.

    Args:
        trigger: The table that triggers a deletion
        link: The linking table between the trigger and the to_delete
        to_delete: The related table
        trigger_identifier: the identifier on the trigger table, that is referenced by the link
            table
        to_delete_identifier: the identifier on the related table that is referenced by the link
            table
        link_from_identifier: the foreign key field on the link table, referencing the trigger table
        link_to_identifier: the foreign key field on the link table, referencing the to_delete table
        other_links: a list of other link tables to determine if a row in to_delete is orphan.
            The same identifier names are assumed on each of these tables.
    """
    trigger_name = trigger.__tablename__
    link_name = link.__tablename__
    delete_name = to_delete.__tablename__
    link_names = {link_name} if other_links is None else {link_name} | set(other_links)
    links_clause = " AND ".join(
        f"""
        NOT EXISTS (
                SELECT 1 FROM {link_name}
                WHERE {link_name}.{link_to_identifier} = {delete_name}.{to_delete_identifier}
        )
        """
        for link_name in link_names
    )
    ddl = DDL(
        f"""
        CREATE TRIGGER delete_{trigger_name}_{delete_name}
        AFTER DELETE ON {trigger_name}
        FOR EACH ROW
        BEGIN
            DELETE FROM {link_name}
            WHERE {link_name}.{link_from_identifier} = OLD.{trigger_identifier};
            DELETE FROM {delete_name}
            WHERE {links_clause};
        END;
        """
    )
    event.listen(trigger.metadata, "after_create", ddl)
