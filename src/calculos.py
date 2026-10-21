import random
import math


def generar_operacion(tipo, dificultad):
    if tipo == 'suma':
        if dificultad == 'facil':
            a = random.randint(5, 20)
            b = random.randint(5, 20)
        elif dificultad == 'medio':
            a = random.randint(10, 50)
            b = random.randint(10, 50)
        else:  # dificil
            a = random.randint(20, 99)
            b = random.randint(10, 50)
        return f"{a} + {b}", a + b

    elif tipo == 'resta':
        if dificultad == 'facil':
            a = random.randint(10, 30)
            b = random.randint(1, a)
        elif dificultad == 'medio':
            a = random.randint(20, 70)
            b = random.randint(5, a)
        else: # dificil
            a = random.randint(50, 99)
            b = random.randint(10, a)
        return f"{a} - {b}", a - b

    elif tipo == 'multiplicacion':
        if dificultad == 'facil':
            a = random.randint(2, 9)
            b = random.randint(2, 9)
        elif dificultad == 'medio':
            a = random.randint(2, 10)
            b = random.randint(10, 15)
        else: # dificil
            a = random.randint(11, 15)
            b = random.randint(2, 9)
        return f"{a} × {b}", a * b

    elif tipo == 'division':
        if dificultad == 'facil':
            b = random.randint(2, 5)
            resultado = random.randint(2, 10)
        elif dificultad == 'medio':
            b = random.randint(2, 9)
            resultado = random.randint(5, 12)
        else: # dificil
            b = random.randint(2, 10)
            resultado = random.randint(10, 15)
        a = b * resultado
        return f"{a} ÷ {b}", resultado

    elif tipo == 'potencias':
        if dificultad == 'facil':
            base = random.randint(2, 5)
            return f"{base}²", base ** 2
        elif dificultad == 'medio':
            base = random.randint(6, 10)
            return f"{base}²", base ** 2
        else: # dificil
            base = random.choice([11, 12, 13, 14, 15, 25])
            return f"{base}²", base ** 2

    elif tipo == 'raices':
        if dificultad == 'facil':
            resultado = random.randint(2, 6)
        elif dificultad == 'medio':
            resultado = random.randint(7, 10)
        else: # dificil
            resultado = random.randint(11, 15)
        a = resultado ** 2
        return f"√{a}", resultado

    return f"2 + 2", 4