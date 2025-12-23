"""Configuration loading and validation for azure-db-zr-bench."""

import os
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass
class BenchmarkTarget:
    """Configuration for a benchmark target database."""

    host: str
    port: int
    database: str
    username: str
    password: str
    service: str  # postgres, mysql, sqldb
    mode: str  # no-ha, samezone-ha, crosszone-ha, non-zr, zr
    ssl_mode: Optional[str] = None
    driver: Optional[str] = None  # For SQL DB ODBC driver

    def __post_init__(self):
        """Validate service and mode values."""
        valid_services = {"postgres", "mysql", "sqldb"}
        if self.service not in valid_services:
            raise ValueError(f"Invalid service: {self.service}. Must be one of {valid_services}")

        valid_modes = {"no-ha", "samezone-ha", "crosszone-ha", "non-zr", "zr"}
        if self.mode not in valid_modes:
            raise ValueError(f"Invalid mode: {self.mode}. Must be one of {valid_modes}")


def resolve_env_vars(value: str) -> str:
    """Resolve environment variable references in config values.

    Supports formats:
    - ${VAR_NAME} - required, raises error if not set
    - ${VAR_NAME:-default} - with default value
    """
    if not isinstance(value, str):
        return value

    import re

    pattern = r"\$\{([^}:]+)(?::-([^}]*))?\}"

    def replace(match):
        var_name = match.group(1)
        default = match.group(2)
        env_value = os.environ.get(var_name)

        if env_value is not None:
            return env_value
        if default is not None:
            return default
        raise ValueError(f"Environment variable {var_name} is not set and no default provided")

    return re.sub(pattern, replace, value)


def load_config(config_path: Path) -> Dict[str, BenchmarkTarget]:
    """Load benchmark targets from a YAML configuration file.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dictionary mapping target names to BenchmarkTarget objects

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    if not config or "targets" not in config:
        raise ValueError("Config file must contain a 'targets' section")

    targets = {}
    for name, target_config in config["targets"].items():
        # Resolve environment variables in string values
        resolved_config = {}
        for key, value in target_config.items():
            resolved_config[key] = resolve_env_vars(value) if isinstance(value, str) else value

        # Set defaults for optional fields
        resolved_config.setdefault("ssl_mode", None)
        resolved_config.setdefault("driver", None)

        targets[name] = BenchmarkTarget(**resolved_config)

    return targets


def get_default_config_template() -> str:
    """Return a template configuration file as a string."""
    return '''# Azure DB Zone Redundancy Benchmark Configuration
# 
# Environment variables can be used with ${VAR_NAME} or ${VAR_NAME:-default}
# Passwords should always use environment variables for security.

targets:
  # PostgreSQL Flexible Server targets
  pg-noha:
    host: "pg-noha-SUFFIX.privatelink.postgres.database.azure.com"
    port: 5432
    database: "benchmark"
    username: "benchadmin"
    password: "${DB_PASSWORD}"
    service: "postgres"
    mode: "no-ha"
    ssl_mode: "require"

  pg-samezoneha:
    host: "pg-szha-SUFFIX.privatelink.postgres.database.azure.com"
    port: 5432
    database: "benchmark"
    username: "benchadmin"
    password: "${DB_PASSWORD}"
    service: "postgres"
    mode: "samezone-ha"
    ssl_mode: "require"

  pg-crosszoneha:
    host: "pg-czha-SUFFIX.privatelink.postgres.database.azure.com"
    port: 5432
    database: "benchmark"
    username: "benchadmin"
    password: "${DB_PASSWORD}"
    service: "postgres"
    mode: "crosszone-ha"
    ssl_mode: "require"

  # MySQL Flexible Server targets
  mysql-noha:
    host: "mysql-noha-SUFFIX.privatelink.mysql.database.azure.com"
    port: 3306
    database: "benchmark"
    username: "benchadmin"
    password: "${DB_PASSWORD}"
    service: "mysql"
    mode: "no-ha"
    ssl_mode: "REQUIRED"

  mysql-samezoneha:
    host: "mysql-szha-SUFFIX.privatelink.mysql.database.azure.com"
    port: 3306
    database: "benchmark"
    username: "benchadmin"
    password: "${DB_PASSWORD}"
    service: "mysql"
    mode: "samezone-ha"
    ssl_mode: "REQUIRED"

  mysql-crosszoneha:
    host: "mysql-czha-SUFFIX.privatelink.mysql.database.azure.com"
    port: 3306
    database: "benchmark"
    username: "benchadmin"
    password: "${DB_PASSWORD}"
    service: "mysql"
    mode: "crosszone-ha"
    ssl_mode: "REQUIRED"

  # Azure SQL Database targets
  sqldb-nonzr:
    host: "sql-zrbench-SUFFIX.privatelink.database.windows.net"
    port: 1433
    database: "sqldb-nonzr"
    username: "benchadmin"
    password: "${DB_PASSWORD}"
    service: "sqldb"
    mode: "non-zr"
    driver: "ODBC Driver 18 for SQL Server"

  sqldb-zr:
    host: "sql-zrbench-SUFFIX.privatelink.database.windows.net"
    port: 1433
    database: "sqldb-zr"
    username: "benchadmin"
    password: "${DB_PASSWORD}"
    service: "sqldb"
    mode: "zr"
    driver: "ODBC Driver 18 for SQL Server"
'''
