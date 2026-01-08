revision = "0000000006"
down_revision = "0000000005"


def upgrade(migration):
    # Create the "task" table
    migration.create_table(
        "task",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "title" varchar(255) NOT NULL,
            "description" text DEFAULT NULL,
            "completed" boolean DEFAULT false,
            "due_date" timestamp DEFAULT NULL,
            "person_id" varchar(32) NOT NULL,
            PRIMARY KEY ("entity_id")
        """
    )
    migration.add_index("task", "task_person_id_ind", "person_id")
    migration.add_index("task", "task_completed_ind", "completed")
    migration.add_index("task", "task_person_id_completed_ind", "person_id, completed")

    # Create the "task_audit" table
    migration.create_table(
        "task_audit",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "title" varchar(255) NOT NULL,
            "description" text DEFAULT NULL,
            "completed" boolean DEFAULT false,
            "due_date" timestamp DEFAULT NULL,
            "person_id" varchar(32) NOT NULL,
            PRIMARY KEY ("entity_id", "version")
        """
    )

    migration.update_version_table(version=revision)


def downgrade(migration):
    # Drop both tables
    migration.drop_table(table_name="task")
    migration.drop_table(table_name="task_audit")

    migration.update_version_table(version=down_revision)
