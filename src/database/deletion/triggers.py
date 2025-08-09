"""
Deletion triggers, to automatically delete rows from related tables.

Note that normally adding cascading deletes is preferable, but that's not always easy because
tables are referenced by multiple tables. See src/README.md for additional information.
"""

from typing import Type

from sqlalchemy import DDL
from sqlmodel import SQLModel

from database.model.helper_functions import get_relationships, non_abstract_subclasses


def create_identifier_synchronization_triggers(dialect: str = "mysql"):
    # Sync triggers make sure all identifiers of an asset are identical.
    # See also: docs/developer/schema/index.md#a_note_on_identifiers

    # These objects are imported here to avoid circular imports,
    # these classes indirectly import triggers through their relationships.
    from database.model.agent.agent import Agent
    from database.model.agent.agent_table import AgentTable
    from database.model.ai_asset.ai_asset import AIAsset
    from database.model.ai_asset.ai_asset_table import AIAssetTable
    from database.model.ai_resource.resource import AIResource
    from database.model.ai_resource.resource_table import AIResourceORM
    from database.model.knowledge_asset.knowledge_asset import KnowledgeAsset
    from database.model.knowledge_asset.knowledge_asset_table import KnowledgeAssetTable

    triggers = []
    for parent_class, reference_table in [
        (AIResource, AIResourceORM),
        (AIAsset, AIAssetTable),
        (Agent, AgentTable),
        (KnowledgeAsset, KnowledgeAssetTable),
    ]:
        parent_table_name = reference_table.__tablename__  # type: ignore[attr-defined]
        for cls in non_abstract_subclasses(parent_class):
            reference_column = f"{parent_table_name}_id"
            msg = f"Cannot create trigger to update {reference_column} on {parent_class} since the column is not defined."
            assert reference_column in parent_class.__fields__, msg  # noqa: S101  # We *want* the server to not start if there are issues here
            sqlite_ddl = DDL(
                f"""
                CREATE TRIGGER IF NOT EXISTS sync_{cls.__tablename__}_{parent_table_name}_identifier
                AFTER INSERT ON {cls.__tablename__}
                BEGIN
                    UPDATE {parent_table_name}
                    SET identifier = NEW.identifier
                    WHERE identifier = NEW.{reference_column};
                END;
                """  # noqa: S608  # never user input
            )
            mysql_ddl = DDL(
                f"""
                CREATE TRIGGER IF NOT EXISTS sync_{cls.__tablename__}_{parent_table_name}_identifier
                AFTER INSERT ON {cls.__tablename__}
                FOR EACH ROW
                BEGIN
                    UPDATE {parent_table_name} SET {parent_table_name}.identifier = NEW.identifier WHERE {parent_table_name}.identifier = NEW.{reference_column};
                END;
                """  # noqa: S608  # never user input
            )
            triggers.append(mysql_ddl if dialect == "mysql" else sqlite_ddl)
    return triggers


def create_delete_triggers(parent_class: Type[SQLModel]):
    classes: list[Type[SQLModel]] = non_abstract_subclasses(parent_class)
    triggers = []
    for cls in classes:
        for name, value in get_relationships(cls).items():
            trigger = value.create_triggers(cls, name)
            if trigger is not None:
                triggers.append(trigger)
    return triggers


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

    return DDL(
        f"""
        CREATE TRIGGER IF NOT EXISTS delete_{trigger_name}_{trigger_identifier_link}_{delete_name}
        AFTER DELETE ON {trigger_name}
        FOR EACH ROW
        BEGIN
            DELETE FROM {delete_name}
            WHERE {delete_name}.{to_delete_identifier} = OLD.{trigger_identifier_link};
        END;
        """  # noqa: S608  # never user input
    )


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

    return DDL(
        f"""
        CREATE TRIGGER IF NOT EXISTS delete_{trigger_name}_{delete_name}
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
        """  # noqa: S608  # never user input
    )


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
        """  # noqa: S608  # never user input
        for link_name in link_names
    )
    return DDL(
        f"""
        CREATE TRIGGER IF NOT EXISTS delete_{link_name}
        AFTER DELETE ON {trigger_name}
        FOR EACH ROW
        BEGIN
            DELETE FROM {link_name}
            WHERE {link_name}.{link_from_identifier} = OLD.{trigger_identifier};
            DELETE FROM {delete_name}
            WHERE {links_clause};
        END;
        """  # noqa: S608  # never user input
    )
