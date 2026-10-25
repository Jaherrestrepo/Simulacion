"""
PROYECTO ACADÉMICO: YAHTZEE CON MONTECARLO
Fases integradas: USA (analiza), MODIFICA (dados cargados), CREA (decisión de riesgo)
y DEBATE (límites de la aproximación).

Requisitos:
- Dos jugadores, cinco dados y hasta tres lanzamientos por turno.
- Modo justo: cada cara tiene probabilidad 1/6.
- Modo cargado: el seis tiene probabilidad 30%; las caras 1–5 comparten el 70%.
- Fase CREA: cuando el jugador tiene tres dados iguales, compara seguir intentando
  con detenerse y puntuar la mejor categoría disponible. La decisión usa Montecarlo.
- Experimento de convergencia para N = 100, 1.000, 10.000 y 100.000 lanzamientos.
- Exportación CSV de resultados.
"""

import random
import csv
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# -------------------- CONFIGURACIÓN --------------------
SEMILLA = 20261025
NUM_PARTIDAS = 30
SIMULACIONES_POR_MASCARA = 100
CARAS = [1, 2, 3, 4, 5, 6]
CATEGORIAS = [
    "unos", "doses", "treses", "cuatros", "cincos", "seises",
    "trio", "poker", "full_house", "escalera_corta",
    "escalera_larga", "yahtzee", "azar"
]
random.seed(SEMILLA)


def lanzar_dado(modo: str = "justo") -> int:
    """Fase 2 MODIFICA: cambia la distribución según el modo elegido."""
    if modo == "justo":
        return random.randint(1, 6)
    if modo == "cargado":
        # P(6)=0.30; P(1..5)=0.14 cada una. Total = 0.30 + 5*0.14 = 1.
        return random.choices(CARAS, weights=[14, 14, 14, 14, 14, 30], k=1)[0]
    raise ValueError("modo debe ser 'justo' o 'cargado'")


def lanzar_dados(dados: List[int], conservar: List[bool], modo: str) -> None:
    for i, queda in enumerate(conservar):
        if not queda:
            dados[i] = lanzar_dado(modo)


def hay_escalera(dados: List[int], longitud: int) -> bool:
    caras = sorted(set(dados))
    racha = mejor = 1
    for i in range(1, len(caras)):
        if caras[i] == caras[i - 1] + 1:
            racha += 1
            mejor = max(mejor, racha)
        else:
            racha = 1
    return mejor >= longitud


def puntuar(categoria: str, dados: List[int]) -> int:
    conteo = Counter(dados)
    frecuencias = sorted(conteo.values())
    suma = sum(dados)
    superiores = {"unos": 1, "doses": 2, "treses": 3, "cuatros": 4, "cincos": 5, "seises": 6}
    if categoria in superiores:
        cara = superiores[categoria]
        return conteo.get(cara, 0) * cara
    if categoria == "trio":
        return suma if any(n >= 3 for n in frecuencias) else 0
    if categoria == "poker":
        return suma if any(n >= 4 for n in frecuencias) else 0
    if categoria == "full_house":
        return 25 if frecuencias == [2, 3] else 0
    if categoria == "escalera_corta":
        return 30 if hay_escalera(dados, 4) else 0
    if categoria == "escalera_larga":
        return 40 if hay_escalera(dados, 5) else 0
    if categoria == "yahtzee":
        return 50 if frecuencias == [5] else 0
    if categoria == "azar":
        return suma
    return 0


def mejor_categoria(dados: List[int], disponibles: List[str]) -> Tuple[str, int]:
    return max(((c, puntuar(c, dados)) for c in disponibles), key=lambda x: x[1])


def mascaras_conservacion() -> List[List[bool]]:
    return [[bool((n >> i) & 1) for i in range(5)] for n in range(32)]


@dataclass
class Jugador:
    nombre: str
    tarjeta: Dict[str, Optional[int]] = field(default_factory=lambda: {c: None for c in CATEGORIAS})

    @property
    def puntos_totales(self) -> int:
        return sum(v for v in self.tarjeta.values() if v is not None)

    def disponibles(self) -> List[str]:
        return [c for c, v in self.tarjeta.items() if v is None]


def valor_esperado(dados: List[int], mascara: List[bool], tiradas_futuras: int,
                   disponibles: List[str], n: int, modo: str) -> float:
    """Estimación Montecarlo con una máscara fija; aproximación heurística, no óptimo exacto."""
    total = 0
    for _ in range(n):
        finales = dados[:]
        for _ in range(tiradas_futuras):
            lanzar_dados(finales, mascara, modo)
        total += mejor_categoria(finales, disponibles)[1]
    return total / n


def elegir_conservacion(dados: List[int], lanzamientos_restantes: int,
                        disponibles: List[str], n: int, modo: str) -> List[bool]:
    # Fase 3 CREA: compara alternativas mediante el valor esperado estimado.
    mejor_mascara, mejor_valor = [True] * 5, -1.0
    for mascara in mascaras_conservacion():
        valor = valor_esperado(dados, mascara, max(0, lanzamientos_restantes - 1), disponibles, n, modo)
        if valor > mejor_valor:
            mejor_mascara, mejor_valor = mascara, valor
    return mejor_mascara


def decidir_trio(dados: List[int], disponibles: List[str], lanzamientos_restantes: int,
                 n: int, modo: str) -> Dict[str, object]:
    """Si ya hay tres iguales, compara detenerse con continuar intentando."""
    conteo = Counter(dados)
    cara_trio = next((cara for cara, cantidad in conteo.items() if cantidad >= 3), None)
    if cara_trio is None:
        return {"tiene_trio": False, "decision": "sin_trio", "valor_detenerse": None, "valor_continuar": None}
    valor_detenerse = mejor_categoria(dados, disponibles)[1]
    mascara = [valor == cara_trio for valor in dados]
    valor_continuar = valor_esperado(dados, mascara, lanzamientos_restantes, disponibles, n, modo)
    decision = "continuar" if valor_continuar > valor_detenerse else "detenerse"
    return {
        "tiene_trio": True, "cara_trio": cara_trio, "decision": decision,
        "valor_detenerse": round(valor_detenerse, 3),
        "valor_continuar": round(valor_continuar, 3)
    }


def jugar_turno(jugador: Jugador, n: int, modo: str, mostrar: bool = False) -> Dict[str, object]:
    dados = [lanzar_dado(modo) for _ in range(5)]
    lanzamiento = 1
    decision_trio = None
    while lanzamiento < 3:
        disponibles = jugador.disponibles()
        decision_trio = decidir_trio(dados, disponibles, 3 - lanzamiento, n, modo)
        if decision_trio["tiene_trio"] and decision_trio["decision"] == "detenerse":
            if mostrar:
                print(f"{jugador.nombre}: decide detenerse con trío. {decision_trio}")
            break
        mascara = elegir_conservacion(dados, 3 - lanzamiento, disponibles, n, modo)
        if all(mascara):
            break
        lanzar_dados(dados, mascara, modo)
        lanzamiento += 1
    categoria, puntos = mejor_categoria(dados, jugador.disponibles())
    jugador.tarjeta[categoria] = puntos
    if mostrar:
        print(f"{jugador.nombre}: dados={dados}; categoría={categoria}; puntos={puntos}")
    return {"dados_finales": dados, "categoria": categoria, "puntos": puntos, "decision_trio": decision_trio}


def jugar_partida(n: int = SIMULACIONES_POR_MASCARA, modo: str = "justo", mostrar: bool = False) -> Dict[str, object]:
    jugadores = [Jugador("Jugador 1"), Jugador("Jugador 2")]
    for _ in range(13):
        for jugador in jugadores:
            jugar_turno(jugador, n, modo, mostrar)
    p1, p2 = jugadores[0].puntos_totales, jugadores[1].puntos_totales
    ganador = "Jugador 1" if p1 > p2 else "Jugador 2" if p2 > p1 else "Empate"
    return {"puntos_jugador_1": p1, "puntos_jugador_2": p2, "ganador": ganador, "modo": modo}


def experimento_partidas(cantidad: int = NUM_PARTIDAS, n: int = SIMULACIONES_POR_MASCARA,
                         modo: str = "justo") -> List[Dict[str, object]]:
    return [{"partida": i, **jugar_partida(n, modo)} for i in range(1, cantidad + 1)]


def experimento_grandes_numeros(tamanos=(100, 1000, 10000, 100000), modo="justo") -> List[Dict[str, object]]:
    """Fase 1 USA: registra la frecuencia empírica de cada cara."""
    resultados = []
    for n in tamanos:
        conteo = Counter(lanzar_dado(modo) for _ in range(n))
        fila = {"N": n}
        for cara in CARAS:
            fila[f"frecuencia_{cara}"] = conteo[cara] / n
        fila["max_desviacion_pp"] = max(abs(conteo[c] / n - 1/6) for c in CARAS) * 100 if modo == "justo" else None
        resultados.append(fila)
    return resultados


def pruebas_basicas() -> None:
    assert lanzar_dado("justo") in CARAS
    assert lanzar_dado("cargado") in CARAS
    assert puntuar("yahtzee", [4, 4, 4, 4, 4]) == 50
    assert puntuar("full_house", [2, 2, 2, 5, 5]) == 25
    assert puntuar("escalera_corta", [1, 2, 3, 4, 6]) == 30
    assert puntuar("escalera_larga", [2, 3, 4, 5, 6]) == 40
    assert len(mascaras_conservacion()) == 32
    print("Pruebas básicas superadas.")


def guardar_csv(nombre: str, filas: List[Dict[str, object]]) -> None:
    if not filas:
        return
    with open(nombre, "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        escritor.writeheader()
        escritor.writerows(filas)


if __name__ == "__main__":
    pruebas_basicas()
    inicio = time.time()
    for modo in ("justo", "cargado"):
        resultados = experimento_partidas(cantidad=NUM_PARTIDAS, modo=modo)
        guardar_csv(f"resultados_{modo}.csv", resultados)
        media1 = sum(r["puntos_jugador_1"] for r in resultados) / len(resultados)
        media2 = sum(r["puntos_jugador_2"] for r in resultados) / len(resultados)
        victorias1 = sum(r["ganador"] == "Jugador 1" for r in resultados) / len(resultados)
        print(f"\nModo {modo}: media J1={media1:.2f}; media J2={media2:.2f}; victorias J1={victorias1:.1%}")
    convergencia = experimento_grandes_numeros()
    guardar_csv("convergencia_grandes_numeros.csv", convergencia)
    print("\nConvergencia (modo justo):")
    for fila in convergencia:
        print(fila)
    print(f"Tiempo total: {time.time()-inicio:.2f} s")
