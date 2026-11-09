CREATE TABLE IF NOT EXISTS universidad.usuarios (
  id uuid PRIMARY KEY,
  nombre text,
  fecha timestamp
);

SELECT * FROM universidad.usuarios;
SELECT COUNT(*) FROM universidad.usuarios;
