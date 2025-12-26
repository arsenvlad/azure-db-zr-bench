"""Database provider implementations for azure-db-zr-bench."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple
import time
import random
import string

from .config import BenchmarkTarget


@dataclass
class WriteResult:
    """Result of a single write operation."""

    success: bool
    latency_ms: float
    rows_written: int
    error: Optional[str] = None
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class DatabaseProvider(ABC):
    """Abstract base class for database providers."""

    def __init__(self, config: BenchmarkTarget):
        self.config = config
        self._connection = None

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the database."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close the database connection."""
        pass

    @abstractmethod
    def create_benchmark_table(self) -> None:
        """Create the benchmark table if it doesn't exist."""
        pass

    @abstractmethod
    def truncate_benchmark_table(self) -> None:
        """Truncate the benchmark table."""
        pass

    @abstractmethod
    def write_batch(self, batch_size: int) -> WriteResult:
        """Write a batch of rows and return the result."""
        pass

    def generate_payload(self, size: int = 512) -> str:
        """Generate a random payload string."""
        return "".join(random.choices(string.ascii_letters + string.digits, k=size))


class PostgresProvider(DatabaseProvider):
    """PostgreSQL database provider using psycopg."""

    def connect(self) -> None:
        import psycopg

        # Build connection string with SSL mode
        conninfo = (
            f"host={self.config.host} "
            f"port={self.config.port} "
            f"dbname={self.config.database} "
            f"user={self.config.username} "
            f"password={self.config.password}"
        )

        # Add SSL mode if specified
        if self.config.ssl_mode:
            conninfo += f" sslmode={self.config.ssl_mode}"

        self._connection = psycopg.connect(conninfo)

        # Set autocommit mode for explicit transaction control
        self._connection.autocommit = False

    def disconnect(self) -> None:
        if self._connection:
            self._connection.close()
            self._connection = None

    def create_benchmark_table(self) -> None:
        with self._connection.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS benchmark_writes (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id INTEGER NOT NULL,
                    ts TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    payload VARCHAR(1024) NOT NULL
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_benchmark_writes_tenant 
                ON benchmark_writes(tenant_id)
            """)
        self._connection.commit()

    def truncate_benchmark_table(self) -> None:
        with self._connection.cursor() as cur:
            cur.execute("TRUNCATE TABLE benchmark_writes")
        self._connection.commit()

    def write_batch(self, batch_size: int) -> WriteResult:
        start_time = time.perf_counter()

        try:
            with self._connection.cursor() as cur:
                if batch_size == 1:
                    # Single row insert
                    cur.execute(
                        "INSERT INTO benchmark_writes (tenant_id, payload) VALUES (%s, %s)",
                        (random.randint(1, 1000), self.generate_payload()),
                    )
                else:
                    # Batch insert using executemany
                    data = [
                        (random.randint(1, 1000), self.generate_payload())
                        for _ in range(batch_size)
                    ]
                    cur.executemany(
                        "INSERT INTO benchmark_writes (tenant_id, payload) VALUES (%s, %s)",
                        data,
                    )

            self._connection.commit()

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return WriteResult(success=True, latency_ms=elapsed_ms, rows_written=batch_size)

        except Exception as e:
            self._connection.rollback()
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return WriteResult(
                success=False, latency_ms=elapsed_ms, rows_written=0, error=str(e)
            )


class MySQLProvider(DatabaseProvider):
    """MySQL database provider using mysql-connector-python."""

    def connect(self) -> None:
        import mysql.connector

        ssl_config = {}
        if self.config.ssl_mode and self.config.ssl_mode.upper() == "REQUIRED":
            ssl_config = {"ssl_disabled": False, "ssl_verify_identity": False}

        self._connection = mysql.connector.connect(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.username,
            password=self.config.password,
            autocommit=False,
            **ssl_config,
        )

    def disconnect(self) -> None:
        if self._connection:
            self._connection.close()
            self._connection = None

    def create_benchmark_table(self) -> None:
        cursor = self._connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS benchmark_writes (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                tenant_id INT NOT NULL,
                ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                payload VARCHAR(1024) NOT NULL,
                INDEX idx_tenant (tenant_id)
            ) ENGINE=InnoDB
        """)
        self._connection.commit()
        cursor.close()

    def truncate_benchmark_table(self) -> None:
        cursor = self._connection.cursor()
        cursor.execute("TRUNCATE TABLE benchmark_writes")
        self._connection.commit()
        cursor.close()

    def write_batch(self, batch_size: int) -> WriteResult:
        start_time = time.perf_counter()
        cursor = None

        try:
            cursor = self._connection.cursor()

            if batch_size == 1:
                cursor.execute(
                    "INSERT INTO benchmark_writes (tenant_id, payload) VALUES (%s, %s)",
                    (random.randint(1, 1000), self.generate_payload()),
                )
            else:
                data = [
                    (random.randint(1, 1000), self.generate_payload())
                    for _ in range(batch_size)
                ]
                cursor.executemany(
                    "INSERT INTO benchmark_writes (tenant_id, payload) VALUES (%s, %s)",
                    data,
                )

            self._connection.commit()

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return WriteResult(success=True, latency_ms=elapsed_ms, rows_written=batch_size)

        except Exception as e:
            self._connection.rollback()
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return WriteResult(
                success=False, latency_ms=elapsed_ms, rows_written=0, error=str(e)
            )

        finally:
            if cursor:
                cursor.close()


class SQLDBProvider(DatabaseProvider):
    """Azure SQL Database provider using pyodbc."""

    def connect(self) -> None:
        import pyodbc

        driver = self.config.driver or "ODBC Driver 18 for SQL Server"

        connection_string = (
            f"DRIVER={{{driver}}};"
            f"SERVER={self.config.host},{self.config.port};"
            f"DATABASE={self.config.database};"
            f"UID={self.config.username};"
            f"PWD={self.config.password};"
            "Encrypt=yes;"
            "TrustServerCertificate=yes;"
            "Connection Timeout=30;"
        )

        self._connection = pyodbc.connect(connection_string, autocommit=False)

    def disconnect(self) -> None:
        if self._connection:
            self._connection.close()
            self._connection = None

    def create_benchmark_table(self) -> None:
        cursor = self._connection.cursor()

        # Check if table exists
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'benchmark_writes')
            BEGIN
                CREATE TABLE benchmark_writes (
                    id BIGINT IDENTITY(1,1) PRIMARY KEY,
                    tenant_id INT NOT NULL,
                    ts DATETIME2 DEFAULT GETUTCDATE(),
                    payload NVARCHAR(1024) NOT NULL
                );
                CREATE INDEX idx_benchmark_writes_tenant ON benchmark_writes(tenant_id);
            END
        """)

        self._connection.commit()
        cursor.close()

    def truncate_benchmark_table(self) -> None:
        cursor = self._connection.cursor()
        cursor.execute("TRUNCATE TABLE benchmark_writes")
        self._connection.commit()
        cursor.close()

    def write_batch(self, batch_size: int) -> WriteResult:
        start_time = time.perf_counter()
        cursor = None

        try:
            cursor = self._connection.cursor()

            if batch_size == 1:
                cursor.execute(
                    "INSERT INTO benchmark_writes (tenant_id, payload) VALUES (?, ?)",
                    (random.randint(1, 1000), self.generate_payload()),
                )
            else:
                data = [
                    (random.randint(1, 1000), self.generate_payload())
                    for _ in range(batch_size)
                ]
                cursor.executemany(
                    "INSERT INTO benchmark_writes (tenant_id, payload) VALUES (?, ?)",
                    data,
                )

            self._connection.commit()

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return WriteResult(success=True, latency_ms=elapsed_ms, rows_written=batch_size)

        except Exception as e:
            self._connection.rollback()
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return WriteResult(
                success=False, latency_ms=elapsed_ms, rows_written=0, error=str(e)
            )

        finally:
            if cursor:
                cursor.close()


def get_provider(config: BenchmarkTarget) -> DatabaseProvider:
    """Factory function to get the appropriate database provider."""
    providers = {
        "postgres": PostgresProvider,
        "mysql": MySQLProvider,
        "sqldb": SQLDBProvider,
    }

    provider_class = providers.get(config.service)
    if not provider_class:
        raise ValueError(f"Unknown service type: {config.service}")

    return provider_class(config)
