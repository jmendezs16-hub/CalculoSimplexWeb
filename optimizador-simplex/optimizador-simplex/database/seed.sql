USE simplex_db;

-- Usuario demo: correo demo@grupo2.com, contraseña demo1234.
-- El valor es un hash generado con werkzeug.security; nunca se guarda la clave plana.
INSERT INTO usuarios (nombre, correo, password_hash)
VALUES (
  'Grupo 2',
  'demo@grupo2.com',
  'scrypt:32768:8:1$K29ZeHR8jvDpjVln$c41a9827dfb2bead9f662589c7e7f5abc3c36470b8c541d8e3232b9ca5ff0b67d73469a617344d6e80a0520fb72e29820d29aba277de0da5b11dde7013746180'
)
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);
SET @usuario_id = LAST_INSERT_ID();

INSERT INTO empresas (usuario_id, nombre, rubro)
SELECT @usuario_id, 'Fábrica de lámparas (ejemplo)', 'Manufactura'
WHERE NOT EXISTS (
  SELECT 1 FROM empresas
  WHERE usuario_id = @usuario_id AND nombre = 'Fábrica de lámparas (ejemplo)'
);
SELECT id INTO @empresa_id FROM empresas
WHERE usuario_id = @usuario_id AND nombre = 'Fábrica de lámparas (ejemplo)'
ORDER BY id LIMIT 1;

INSERT INTO productos (empresa_id, codigo, nombre, beneficio_unitario)
VALUES
  (@empresa_id, 'L1', 'Lámpara modelo L1', 15),
  (@empresa_id, 'L2', 'Lámpara modelo L2', 10)
ON DUPLICATE KEY UPDATE nombre = VALUES(nombre);
SELECT id INTO @producto_l1 FROM productos WHERE empresa_id = @empresa_id AND codigo = 'L1';
SELECT id INTO @producto_l2 FROM productos WHERE empresa_id = @empresa_id AND codigo = 'L2';

INSERT INTO recursos (empresa_id, nombre, unidad, disponible)
SELECT @empresa_id, 'Trabajo manual', 'minutos', 6000
WHERE NOT EXISTS (
  SELECT 1 FROM recursos WHERE empresa_id = @empresa_id AND nombre = 'Trabajo manual'
);
INSERT INTO recursos (empresa_id, nombre, unidad, disponible)
SELECT @empresa_id, 'Trabajo de máquina', 'minutos', 4800
WHERE NOT EXISTS (
  SELECT 1 FROM recursos WHERE empresa_id = @empresa_id AND nombre = 'Trabajo de máquina'
);
SELECT id INTO @recurso_manual FROM recursos WHERE empresa_id = @empresa_id AND nombre = 'Trabajo manual' ORDER BY id LIMIT 1;
SELECT id INTO @recurso_maquina FROM recursos WHERE empresa_id = @empresa_id AND nombre = 'Trabajo de máquina' ORDER BY id LIMIT 1;

INSERT INTO consumos (producto_id, recurso_id, cantidad)
VALUES
  (@producto_l1, @recurso_manual, 20),
  (@producto_l1, @recurso_maquina, 20),
  (@producto_l2, @recurso_manual, 30),
  (@producto_l2, @recurso_maquina, 10)
ON DUPLICATE KEY UPDATE cantidad = VALUES(cantidad);
