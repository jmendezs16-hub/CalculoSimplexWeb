CREATE DATABASE IF NOT EXISTS simplex_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE simplex_db;

CREATE TABLE IF NOT EXISTS usuarios (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  nombre        VARCHAR(100) NOT NULL,
  correo        VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  creado_en     DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS empresas (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  usuario_id INT NOT NULL,
  nombre     VARCHAR(150) NOT NULL,
  rubro      VARCHAR(100),
  moneda     VARCHAR(10) DEFAULT 'Q',
  periodo    ENUM('diario','semanal','mensual','anual') DEFAULT 'mensual',
  activa     BOOLEAN DEFAULT TRUE,
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS productos (
  id                 INT AUTO_INCREMENT PRIMARY KEY,
  empresa_id         INT NOT NULL,
  codigo             VARCHAR(20) NOT NULL,
  nombre             VARCHAR(150) NOT NULL,
  beneficio_unitario DECIMAL(12,4) NOT NULL,
  activo             BOOLEAN DEFAULT TRUE,
  UNIQUE (empresa_id, codigo),
  FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS recursos (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  empresa_id  INT NOT NULL,
  nombre      VARCHAR(150) NOT NULL,
  unidad      VARCHAR(30) NOT NULL,
  disponible  DECIMAL(14,4) NOT NULL CHECK (disponible >= 0),
  FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS consumos (
  producto_id INT NOT NULL,
  recurso_id  INT NOT NULL,
  cantidad    DECIMAL(14,4) NOT NULL CHECK (cantidad >= 0),
  PRIMARY KEY (producto_id, recurso_id),
  FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
  FOREIGN KEY (recurso_id)  REFERENCES recursos(id)  ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS escenarios (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  empresa_id INT NOT NULL,
  nombre     VARCHAR(150) NOT NULL,
  periodo    VARCHAR(60),
  objetivo   ENUM('max','min') NOT NULL DEFAULT 'max',
  creado_en  DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS escenario_productos (
  escenario_id     INT NOT NULL,
  producto_id      INT NOT NULL,
  incluido         BOOLEAN DEFAULT TRUE,
  produccion_min   DECIMAL(14,4) NULL,
  demanda_max      DECIMAL(14,4) NULL,
  PRIMARY KEY (escenario_id, producto_id),
  FOREIGN KEY (escenario_id) REFERENCES escenarios(id) ON DELETE CASCADE,
  FOREIGN KEY (producto_id)  REFERENCES productos(id)  ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS escenario_recursos (
  escenario_id INT NOT NULL,
  recurso_id   INT NOT NULL,
  disponible   DECIMAL(14,4) NOT NULL,
  PRIMARY KEY (escenario_id, recurso_id),
  FOREIGN KEY (escenario_id) REFERENCES escenarios(id) ON DELETE CASCADE,
  FOREIGN KEY (recurso_id)   REFERENCES recursos(id)   ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS resultados (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  escenario_id  INT NOT NULL UNIQUE,
  estado        ENUM('optimo','infactible','no_acotado','multiple','degenerado') NOT NULL,
  valor_z       DECIMAL(16,4) NULL,
  iteraciones_n INT NOT NULL DEFAULT 0,
  calculado_en  DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (escenario_id) REFERENCES escenarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS resultado_variables (
  resultado_id INT NOT NULL,
  producto_id  INT NOT NULL,
  valor        DECIMAL(16,4) NOT NULL,
  aporte       DECIMAL(16,4) NOT NULL,
  PRIMARY KEY (resultado_id, producto_id),
  FOREIGN KEY (resultado_id) REFERENCES resultados(id) ON DELETE CASCADE,
  FOREIGN KEY (producto_id)  REFERENCES productos(id)
);

CREATE TABLE IF NOT EXISTS resultado_recursos (
  resultado_id   INT NOT NULL,
  recurso_id     INT NOT NULL,
  usado          DECIMAL(16,4) NOT NULL,
  holgura        DECIMAL(16,4) NOT NULL,
  precio_sombra  DECIMAL(16,6) NOT NULL,
  PRIMARY KEY (resultado_id, recurso_id),
  FOREIGN KEY (resultado_id) REFERENCES resultados(id) ON DELETE CASCADE,
  FOREIGN KEY (recurso_id)   REFERENCES recursos(id)
);

CREATE TABLE IF NOT EXISTS recomendaciones (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  resultado_id INT NOT NULL,
  orden        INT NOT NULL,
  titulo       VARCHAR(200) NOT NULL,
  detalle      VARCHAR(500) NOT NULL,
  destacada    BOOLEAN DEFAULT FALSE,
  FOREIGN KEY (resultado_id) REFERENCES resultados(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS iteraciones (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  resultado_id INT NOT NULL,
  numero       INT NOT NULL,
  tabla_json   JSON NOT NULL,
  entra        VARCHAR(20),
  sale         VARCHAR(20),
  explicacion  TEXT,
  FOREIGN KEY (resultado_id) REFERENCES resultados(id) ON DELETE CASCADE
);
