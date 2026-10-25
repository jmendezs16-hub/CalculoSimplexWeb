-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 23-10-2026 a las 03:48:03
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `simplex_db`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `consumos`
--

CREATE TABLE `consumos` (
  `producto_id` int(11) NOT NULL,
  `recurso_id` int(11) NOT NULL,
  `cantidad` decimal(14,4) NOT NULL
) ;

--
-- Volcado de datos para la tabla `consumos`
--

INSERT INTO `consumos` (`producto_id`, `recurso_id`, `cantidad`) VALUES
(1, 1, 20.0000),
(1, 2, 20.0000),
(2, 1, 30.0000),
(2, 2, 10.0000);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `empresas`
--

CREATE TABLE `empresas` (
  `id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `nombre` varchar(150) NOT NULL,
  `rubro` varchar(100) DEFAULT NULL,
  `moneda` varchar(10) DEFAULT 'Q',
  `periodo` enum('diario','semanal','mensual','anual') DEFAULT 'mensual',
  `activa` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `empresas`
--

INSERT INTO `empresas` (`id`, `usuario_id`, `nombre`, `rubro`, `moneda`, `periodo`, `activa`) VALUES
(1, 1, 'Fábrica de lámparas (ejemplo)', 'Manufactura', 'Q', 'mensual', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `escenarios`
--

CREATE TABLE `escenarios` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `nombre` varchar(150) NOT NULL,
  `periodo` varchar(60) DEFAULT NULL,
  `objetivo` enum('max','min') NOT NULL DEFAULT 'max',
  `creado_en` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `escenario_productos`
--

CREATE TABLE `escenario_productos` (
  `escenario_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `incluido` tinyint(1) DEFAULT 1,
  `produccion_min` decimal(14,4) DEFAULT NULL,
  `demanda_max` decimal(14,4) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `escenario_recursos`
--

CREATE TABLE `escenario_recursos` (
  `escenario_id` int(11) NOT NULL,
  `recurso_id` int(11) NOT NULL,
  `disponible` decimal(14,4) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `iteraciones`
--

CREATE TABLE `iteraciones` (
  `id` int(11) NOT NULL,
  `resultado_id` int(11) NOT NULL,
  `numero` int(11) NOT NULL,
  `tabla_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`tabla_json`)),
  `entra` varchar(20) DEFAULT NULL,
  `sale` varchar(20) DEFAULT NULL,
  `explicacion` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `productos`
--

CREATE TABLE `productos` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `codigo` varchar(20) NOT NULL,
  `nombre` varchar(150) NOT NULL,
  `beneficio_unitario` decimal(12,4) NOT NULL,
  `activo` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `productos`
--

INSERT INTO `productos` (`id`, `empresa_id`, `codigo`, `nombre`, `beneficio_unitario`, `activo`) VALUES
(1, 1, 'L1', 'Lámpara modelo L1', 15.0000, 1),
(2, 1, 'L2', 'Lámpara modelo L2', 10.0000, 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `recomendaciones`
--

CREATE TABLE `recomendaciones` (
  `id` int(11) NOT NULL,
  `resultado_id` int(11) NOT NULL,
  `orden` int(11) NOT NULL,
  `titulo` varchar(200) NOT NULL,
  `detalle` varchar(500) NOT NULL,
  `destacada` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `recursos`
--

CREATE TABLE `recursos` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `nombre` varchar(150) NOT NULL,
  `unidad` varchar(30) NOT NULL,
  `disponible` decimal(14,4) NOT NULL
) ;

--
-- Volcado de datos para la tabla `recursos`
--

INSERT INTO `recursos` (`id`, `empresa_id`, `nombre`, `unidad`, `disponible`) VALUES
(1, 1, 'Trabajo manual', 'minutos', 6000.0000),
(2, 1, 'Trabajo de máquina', 'minutos', 4800.0000);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `resultados`
--

CREATE TABLE `resultados` (
  `id` int(11) NOT NULL,
  `escenario_id` int(11) NOT NULL,
  `estado` enum('optimo','infactible','no_acotado','multiple','degenerado') NOT NULL,
  `valor_z` decimal(16,4) DEFAULT NULL,
  `iteraciones_n` int(11) NOT NULL DEFAULT 0,
  `calculado_en` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `resultado_recursos`
--

CREATE TABLE `resultado_recursos` (
  `resultado_id` int(11) NOT NULL,
  `recurso_id` int(11) NOT NULL,
  `usado` decimal(16,4) NOT NULL,
  `holgura` decimal(16,4) NOT NULL,
  `precio_sombra` decimal(16,6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `resultado_variables`
--

CREATE TABLE `resultado_variables` (
  `resultado_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `valor` decimal(16,4) NOT NULL,
  `aporte` decimal(16,4) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `correo` varchar(150) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `creado_en` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `usuarios`
--

INSERT INTO `usuarios` (`id`, `nombre`, `correo`, `password_hash`, `creado_en`) VALUES
(1, 'Grupo 2', 'demo@grupo2.com', 'scrypt:32768:8:1$K29ZeHR8jvDpjVln$c41a9827dfb2bead9f662589c7e7f5abc3c36470b8c541d8e3232b9ca5ff0b67d73469a617344d6e80a0520fb72e29820d29aba277de0da5b11dde7013746180', '2026-10-22 02:48:05');

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `consumos`
--
ALTER TABLE `consumos`
  ADD PRIMARY KEY (`producto_id`,`recurso_id`),
  ADD KEY `recurso_id` (`recurso_id`);

--
-- Indices de la tabla `empresas`
--
ALTER TABLE `empresas`
  ADD PRIMARY KEY (`id`),
  ADD KEY `usuario_id` (`usuario_id`);

--
-- Indices de la tabla `escenarios`
--
ALTER TABLE `escenarios`
  ADD PRIMARY KEY (`id`),
  ADD KEY `empresa_id` (`empresa_id`);

--
-- Indices de la tabla `escenario_productos`
--
ALTER TABLE `escenario_productos`
  ADD PRIMARY KEY (`escenario_id`,`producto_id`),
  ADD KEY `producto_id` (`producto_id`);

--
-- Indices de la tabla `escenario_recursos`
--
ALTER TABLE `escenario_recursos`
  ADD PRIMARY KEY (`escenario_id`,`recurso_id`),
  ADD KEY `recurso_id` (`recurso_id`);

--
-- Indices de la tabla `iteraciones`
--
ALTER TABLE `iteraciones`
  ADD PRIMARY KEY (`id`),
  ADD KEY `resultado_id` (`resultado_id`);

--
-- Indices de la tabla `productos`
--
ALTER TABLE `productos`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_productos_empresa_codigo` (`empresa_id`,`codigo`);

--
-- Indices de la tabla `recomendaciones`
--
ALTER TABLE `recomendaciones`
  ADD PRIMARY KEY (`id`),
  ADD KEY `resultado_id` (`resultado_id`);

--
-- Indices de la tabla `recursos`
--
ALTER TABLE `recursos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `empresa_id` (`empresa_id`);

--
-- Indices de la tabla `resultados`
--
ALTER TABLE `resultados`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `escenario_id` (`escenario_id`);

--
-- Indices de la tabla `resultado_recursos`
--
ALTER TABLE `resultado_recursos`
  ADD PRIMARY KEY (`resultado_id`,`recurso_id`),
  ADD KEY `recurso_id` (`recurso_id`);

--
-- Indices de la tabla `resultado_variables`
--
ALTER TABLE `resultado_variables`
  ADD PRIMARY KEY (`resultado_id`,`producto_id`),
  ADD KEY `producto_id` (`producto_id`);

--
-- Indices de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `correo` (`correo`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `empresas`
--
ALTER TABLE `empresas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de la tabla `escenarios`
--
ALTER TABLE `escenarios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `iteraciones`
--
ALTER TABLE `iteraciones`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `productos`
--
ALTER TABLE `productos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `recomendaciones`
--
ALTER TABLE `recomendaciones`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `recursos`
--
ALTER TABLE `recursos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `resultados`
--
ALTER TABLE `resultados`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `consumos`
--
ALTER TABLE `consumos`
  ADD CONSTRAINT `consumos_ibfk_1` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `consumos_ibfk_2` FOREIGN KEY (`recurso_id`) REFERENCES `recursos` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `empresas`
--
ALTER TABLE `empresas`
  ADD CONSTRAINT `empresas_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `escenarios`
--
ALTER TABLE `escenarios`
  ADD CONSTRAINT `escenarios_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `escenario_productos`
--
ALTER TABLE `escenario_productos`
  ADD CONSTRAINT `escenario_productos_ibfk_1` FOREIGN KEY (`escenario_id`) REFERENCES `escenarios` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `escenario_productos_ibfk_2` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `escenario_recursos`
--
ALTER TABLE `escenario_recursos`
  ADD CONSTRAINT `escenario_recursos_ibfk_1` FOREIGN KEY (`escenario_id`) REFERENCES `escenarios` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `escenario_recursos_ibfk_2` FOREIGN KEY (`recurso_id`) REFERENCES `recursos` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `iteraciones`
--
ALTER TABLE `iteraciones`
  ADD CONSTRAINT `iteraciones_ibfk_1` FOREIGN KEY (`resultado_id`) REFERENCES `resultados` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `productos`
--
ALTER TABLE `productos`
  ADD CONSTRAINT `productos_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `recomendaciones`
--
ALTER TABLE `recomendaciones`
  ADD CONSTRAINT `recomendaciones_ibfk_1` FOREIGN KEY (`resultado_id`) REFERENCES `resultados` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `recursos`
--
ALTER TABLE `recursos`
  ADD CONSTRAINT `recursos_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `resultados`
--
ALTER TABLE `resultados`
  ADD CONSTRAINT `resultados_ibfk_1` FOREIGN KEY (`escenario_id`) REFERENCES `escenarios` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `resultado_recursos`
--
ALTER TABLE `resultado_recursos`
  ADD CONSTRAINT `resultado_recursos_ibfk_1` FOREIGN KEY (`resultado_id`) REFERENCES `resultados` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `resultado_recursos_ibfk_2` FOREIGN KEY (`recurso_id`) REFERENCES `recursos` (`id`);

--
-- Filtros para la tabla `resultado_variables`
--
ALTER TABLE `resultado_variables`
  ADD CONSTRAINT `resultado_variables_ibfk_1` FOREIGN KEY (`resultado_id`) REFERENCES `resultados` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `resultado_variables_ibfk_2` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
