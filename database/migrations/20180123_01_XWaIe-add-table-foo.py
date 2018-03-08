"""
Add table foo
"""

from yoyo import step

__depends__ = {}

steps = [
    step(
        "CREATE TABLE foo (id INT, bar VARCHAR(20), PRIMARY KEY (id))",
        "DROP TABLE IF EXISTS foo",
    )
]

