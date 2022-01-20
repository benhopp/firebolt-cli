import os
import sys

from click import command, confirm, echo, group, option
from firebolt.common import Settings
from firebolt.common.exception import FireboltError
from firebolt.service.manager import ResourceManager
from pydantic import ValidationError

from firebolt_cli.common_options import common_options
from firebolt_cli.utils import prepare_execution_result


@group()
def database() -> None:
    """
    Manage the databases using the python-cli
    """


@command()
@common_options
@option("--name", help="New database name", type=str)
@option(
    "--description",
    help="Database textual description up to 64 characters",
    type=str,
    default="",
)
@option("--json", help="Use json for output", default=False, is_flag=True)
@option("--region", help="Region for the new database", default="us-east-1", type=str)
@option(
    "--json",
    is_flag=True,
    help="Provide output in json format",
)
def create(**raw_config_options: str) -> None:
    """
    Create a new database
    """
    settings = Settings(
        server=raw_config_options["api_endpoint"],
        user=raw_config_options["username"],
        password=raw_config_options["password"],
        default_region=raw_config_options["region"],
    )

    try:
        rm = ResourceManager(settings=settings)

        database = rm.databases.create(
            name=raw_config_options["name"],
            description=raw_config_options["description"],
            region=raw_config_options["region"],
        )

        echo(
            "Database {name} is successfully created".format(name=database.name),
            err=True,
        )
        echo(
            prepare_execution_result(
                dict(
                    {
                        "name": database.name,
                        "description": database.description,
                        "create_time": str(database.create_time),
                    }
                ),
                use_json=bool(raw_config_options["json"]),
            )
        )

    except RuntimeError as err:
        echo(err, err=True)
        sys.exit(os.EX_DATAERR)
    except ValidationError as err:
        echo(err, err=True)
        sys.exit(os.EX_DATAERR)


@command()
@common_options
@option("--name", help="Database name, that should be dropped", type=str, required=True)
@option(
    "--yes",
    help="Automatic yes on confirmation prompt",
    is_flag=True,
)
def drop(**raw_config_options: str) -> None:
    """
    Drop an existing database
    """
    settings = Settings(
        server=raw_config_options["api_endpoint"],
        user=raw_config_options["username"],
        password=raw_config_options["password"],
        default_region="",
    )

    try:
        rm = ResourceManager(settings=settings)
        database = rm.databases.get_by_name(name=raw_config_options["name"])

        if raw_config_options["yes"] or confirm(
            "Do you really want to drop the database {name}?".format(
                name=raw_config_options["name"]
            )
        ):
            database.delete()
            echo(
                "Drop request for database {name} is successfully sent".format(
                    name=raw_config_options["name"]
                )
            )
        else:
            echo("Drop request is aborted")

    except (RuntimeError, FireboltError) as err:
        echo(err, err=True)
        sys.exit(os.EX_DATAERR)


database.add_command(create)
database.add_command(drop)
