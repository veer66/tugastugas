"""add undo function

Revision ID: fce4251eee5b
Revises: 6c41dc7e9a66
Create Date: 2024-05-19 12:10:19.100797+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.schema import DDL


# revision identifiers, used by Alembic.
revision: str = 'fce4251eee5b'
down_revision: Union[str, None] = '6c41dc7e9a66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    ddl = DDL("""
CREATE OR REPLACE FUNCTION undo_task_action(expect_user_id INT) RETURNS RECORD AS $$
DECLARE op_type INT;
DECLARE body JSONB;
  h_task_id INT;
  task_id INT;
  stmt TEXT;
  k TEXT;
  v TEXT;
  stmt_state INT;
BEGIN
  SELECT "id",
  	 "data_after_executed_operation",
	 "executed_operation",
	 "target_row_id"
	 INTO h_task_id, body, op_type, task_id
	 FROM h_task
     WHERE user_id = expect_user_id AND not used
	 ORDER BY operation_executed_at DESC
	 LIMIT 1;
  IF task_id IS NULL
  THEN
    RETURN NULL;
  END IF;
  IF op_type = 1 -- INSERT
  THEN
     stmt := 'DELETE FROM task WHERE id = ' || quote_literal(task_id);
     EXECUTE stmt;
  ELSIF op_type = 2 -- DELETE
  THEN
    stmt := 'INSERT INTO task(';
    stmt_state := 1;
    FOR k IN SELECT jsonb_object_keys(body)
    LOOP
      IF stmt_state = 1
      THEN
        stmt_state := 2;
      ELSE
        stmt := stmt || ',';
      END IF;
      stmt := stmt || quote_ident(k);
    END LOOP;

    stmt := stmt || ') VALUES (';

    FOR k IN SELECT jsonb_object_keys(body)
    LOOP
      v := body ->> k;
      IF stmt_state = 2
      THEN
        stmt_state = 3;
      ELSE
	stmt := stmt || ',';
      END IF;
      stmt := stmt || quote_literal(v);
    END LOOP;

    stmt := stmt || ')';
    EXECUTE stmt;
  ELSIF op_type = 3 -- UPDATE
  THEN
    FOR k IN SELECT jsonb_object_keys(body)
    LOOP
      v := body ->> k;
      IF stmt IS NULL
      THEN
        stmt := 'UPDATE task SET ';
      ELSE
        stmt := stmt || ', ';
      END IF;
      stmt := stmt || quote_ident(k) || ' = ' || quote_literal(v);
    END LOOP;
    stmt := stmt || ' WHERE id = ' || quote_literal(task_id);
    EXECUTE stmt;
  END IF;
  UPDATE h_task SET used = true WHERE id = h_task_id;
  RETURN ROW(op_type, task_id);
END;
$$ LANGUAGE plpgsql;
    """)
    op.execute(ddl)


def downgrade() -> None:
    ddl = DDL("DROP FUNCTION undo_task_action")
    op.execute(ddl)
