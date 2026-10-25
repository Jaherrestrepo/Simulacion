# Yahtzee con Montecarlo — Entrega actualizada

## Contenido
- `simulacion_yahtzee_montecarlo.py`: simulador con dados justos y cargados, decisión de riesgo cuando hay tres iguales, pruebas básicas y experimento de la Ley de los Grandes Números.
- `reporte_fases_USA_MODIFICA_CREA_DEBATE.html`: reporte académico interactivo con explicación de las cuatro fases y guion resumido.
- `Guion_video_5_minutos.txt`: texto de apoyo para grabar el video.
- `resultados_justo.csv`, `resultados_cargado.csv`: se generan al ejecutar el script.
- `convergencia_grandes_numeros.csv`: se genera al ejecutar el script.

## Ejecutar
Requiere Python 3.10 o superior. No requiere librerías externas.
```bash
python simulacion_yahtzee_montecarlo.py
```
Los CSV se guardan en el directorio desde el que se ejecuta el script.

## Decisiones y límites
- En modo cargado: P(6)=0.30 y P(1)=...=P(5)=0.14.
- En el experimento de convergencia se compara con 1/6 solo para el modo justo.
- La estrategia Montecarlo es una heurística aproximada: evalúa máscaras de conservación con una decisión fija durante la simulación.
- No incluye todos los bonos opcionales de las reglas comerciales de Yahtzee; documentar este alcance en el informe.
- Para el informe final, añadir nombre, curso, docente y fecha, y ejecutar el código para usar los CSV propios como evidencia.
