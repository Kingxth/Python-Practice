import random
import math

historico = []

def generar_operacion(tipo, dificultad):
    global historico
    
    for _ in range(10):
        pregunta, respuesta, subtema = _generar_logica(tipo, dificultad)
        if pregunta not in historico:
            historico.append(pregunta)
            if len(historico) > 3:
                historico.pop(0)
            return pregunta, respuesta, subtema
            
    return pregunta, respuesta, subtema

def _generar_logica(tipo, dificultad):
    
    #SUMA
    
    if tipo == 'suma':
        if dificultad == 'facil':
            n1 = random.randint(1, 50)
            n2 = random.randint(1, n1)
        elif dificultad == 'medio':
            n1 = random.randint(10, 999)
            n2 = random.randint(10, 999)
        else: # dificil
            n1 = random.randint(10, 9999)
            n2 = random.randint(10, 9999)
        return f"{n1} + {n2}", n1 + n2, "suma"

    # RESTA
    if tipo == 'resta':
        if dificultad == 'facil':
            n1 = random.randint(10, 50)
            n2 = random.randint(1, n1)
        elif dificultad == 'medio':
            n1 = random.randint(-50, 50)
            n2 = random.randint(-50, 50)
        else:
            n1 = random.randint(-999, 999)
            n2 = random.randint(-999, 999)

        if n2 < 0:
            operacion = f"{n1} + {abs(n2)}"
        else:
            operacion = f"{n1} - {n2}"

        return operacion, n1 - n2, "resta"

    # MULTIPLICACION
    if tipo == 'multiplicacion':
        if dificultad == 'facil':
            n1 = random.randint(2, 12)
            n2 = random.randint(2, 12)
        elif dificultad == 'medio':
            n1 = random.randint(10, 30)
            n2 = random.randint(5, 25)
        else: # dificil
            n1 = random.randint(2, 99)
            n2 = random.randint(2, 99)
        return f"{n1} × {n2}", n1 * n2, "multiplicacion"

    # DIVISION
    if tipo == 'division':
        if dificultad == 'facil':
            n2 = random.randint(2, 5)
            res = random.randint(1, 5)
        elif dificultad == 'medio':
            n2 = random.randint(6, 10)
            res = random.randint(2, 9)
        else: # dificil
            n2 = random.randint(11, 15)
            res = random.randint(2, 12)
        return f"{res * n2} / {n2}", res, "division"

    # POTENCIAS
    if tipo == 'potencias':
        if dificultad == 'facil':
            base = random.randint(1, 12)
            exp = 2
        elif dificultad == 'medio':
            num = random.choice([1, 2])
            if num == 1:
                base = 2
                exp = random.randint(0, 9)
            else:
                base = random.randint(1, 10)
                exp = random.choice([2, 3])
        else: # dificil
            base = random.randint(2, 15)
            exp = random.choice([2, 3])
        return f"{base}^{exp}", base ** exp, "potencias"

    # RAICES
    if tipo == 'raices':
        if dificultad == 'facil':
            base = random.randint(2, 10)
        elif dificultad == 'medio':
            base = random.randint(8, 13)
        else: # dificil
            base = random.randint(9, 15)
        return f"√{base**2}", base, "raices"
    
    # Prop. de potencias
    if tipo == 'prop_potencias': 
        base = random.randint(2, 6)
        subtipo = random.choice(['multiplicacion', 'division', 'potencia_potencia'])
        
        if subtipo == 'multiplicacion':
            if dificultad == 'facil':
                e1, e2 = random.randint(1, 15), random.randint(1, 15)
            elif dificultad == 'medio':
                e1, e2 = random.randint(15, 45), random.randint(9, 45)
            else:
                e1, e2 = random.randint(3, 99), random.randint(3, 99)
            
            pregunta = f"<span style='white-space: nowrap;'>{base}<sup>{e1}</sup>&nbsp; * &nbsp;{base}<sup>{e2}</sup>&nbsp;=&nbsp;{base}<sup>x</sup></span>"
            respuesta = e1 + e2
            
        elif subtipo == 'division':
            if dificultad == 'facil':
                e2 = random.randint(1, 5)
                e1 = random.randint(5, 10)
            elif dificultad == 'medio':
                e2 = random.randint(2, 16)
                e1 = random.randint(9, 20)
            else:
                e2 = random.randint(3, 25)
                e1 = random.randint(4, 25)
                
            pregunta = f"<span style='white-space: nowrap;'>{base}<sup>{e1}</sup>&nbsp;&divide;&nbsp;{base}<sup>{e2}</sup>&nbsp;=&nbsp;{base}<sup>x</sup></span>"
            respuesta = e1 - e2
            
        else: # potencia_potencia
            if dificultad == 'facil':
                e1, e2 = random.randint(2, 8), 2
            elif dificultad == 'medio':
                e1, e2 = random.randint(2, 10), random.randint(2, 5)
            else:
                e1, e2 = random.randint(2, 15), random.randint(3, 9)
                
            pregunta = f"<span style='white-space: nowrap;'>({base}<sup>{e1}</sup>)<sup>{e2}</sup>&nbsp;=&nbsp;{base}<sup>x</sup></span>"
            respuesta = e1 * e2
            
        return pregunta, respuesta, f"prop_{subtipo}"

    # SEN / COS
    if tipo == 'sencos':
        if dificultad == 'facil':
            ang = random.choice([0, 90])
        elif dificultad == 'medio':
            ang = random.choice([0, 30, 45, 60, 90])
        else:
            ang = random.choice([0, 30, 45, 60, 90, 180])
        
        op = random.choice(['sin', 'cos'])
        if op == 'sin':
            res = round(math.sin(math.radians(ang)))
        else:
            res = round(math.cos(math.radians(ang)))
        return f"{op}({ang}°)", res, "sencos"

    # ECUACIONES DE 1ER GRADO
    if tipo == 'ecuacion_1er_grado':
        subtipo = random.choice(['entero', 'fraccion_homogenea', 'fraccion_heterogenea'])
        
        if subtipo == 'entero':
            a = random.randint(2, 9)
            x = random.randint(-10, 10)
            b = random.randint(-20, 20)
            c = a * x + b
            
            signo_b = "+" if b >= 0 else "-"
            pregunta = f"{a}x {signo_b} {abs(b)} = {c}"
            respuesta = str(x)
            
        elif subtipo == 'fraccion_homogenea':
            d = random.choice([2, 3, 4, 5])
            a = random.randint(2, 6)
            x = random.randint(1, 10)
            b = random.randint(1, 10)
            c = a * x + b
            pregunta = (
                f'<span class="frac"><span class="numerator">{a}x + {b}</span><span class="denominator">{d}</span></span> '
                f'= <span class="frac"><span class="numerator">{c}</span><span class="denominator">{d}</span></span>'
            )
            respuesta = str(x)
            
        else: # fraccion heterogenea
            a = random.choice([2, 3, 4])
            x = a * random.randint(1, 5) 
            b = random.randint(1, 10)
            c = (x // a) + b
            
            pregunta = f'<span class="frac"><span class="numerator">x</span><span class="denominator">{a}</span></span> + {b} = {c}'
            respuesta = str(x)
            
        return pregunta, respuesta, f"ecuacion_1er_{subtipo}"

    # ECUACIONES DE SEGUNDO GRADO
    if tipo == 'ecuacion_2do_grado':
        r1 = random.randint(-5, 5)
        r2 = random.randint(-5, 5)
        while r1 == r2:
            r2 = random.randint(-5, 5)
            
        suma_r = r1 + r2
        prod_r = r1 * r2
        
        s1 = f"- {abs(suma_r)}x" if suma_r > 0 else f"+ {abs(suma_r)}x" if suma_r < 0 else ""
        if suma_r == 0:
            s1 = ""
            
        s2 = f"+ {prod_r}" if prod_r > 0 else f"- {abs(prod_r)}" if prod_r < 0 else ""
        
        pregunta = f"x² {s1} {s2} = 0".replace("  ", " ")
        
        raices = sorted([r1, r2])
        respuesta = f"{raices[0]}, {raices[1]}"
        
        return pregunta, respuesta, "ecuacion_2do_grado"

    # FACTORIZACION
    if tipo == 'factorizacion':
        caso = random.choice(['factor_comun', 'trinomio_cuadrado', 'diferencia_cuadrados'])
        
        if caso == 'factor_comun':
            comun = random.randint(2, 5)
            coef = random.randint(2, 6)
            termino = random.randint(1, 8)
            pregunta = f"{comun * coef}x² + {comun * termino}x"
            respuesta = f"{comun}x(x + {termino // comun})" if termino % comun == 0 else f"{comun}x({coef}x + {termino})"
            
        elif caso == 'trinomio_cuadrado':
            a = random.randint(1, 8)
            b_coef = 2 * a
            c_term = a ** 2
            pregunta = f"x² + {b_coef}x + {c_term}"
            respuesta = f"(x + {a})²"
            
        else: # diferencia de cuadrados
            a = random.randint(1, 10)
            a2 = a ** 2
            pregunta = f"x² - {a2}"
            respuesta = f"(x - {a})(x + {a})"
            
        return pregunta, respuesta, f"factorizacion_{caso}"

    # DERIVADAS
    if tipo == 'derivadas':
        caso = random.choice(['polinomio', 'exponencial', 'trigonometrica', 'logaritmica'])
        
        if caso == 'polinomio':
            a = random.randint(2, 6)
            n = random.randint(2, 4)
            coef = a * n
            nuevo_n = n - 1
            if nuevo_n == 1:
                pregunta = f"d/dx ({a}x<sup>{n}</sup>)"
                respuesta = f"{coef}x"
            else:
                pregunta = f"d/dx ({a}x<sup>{n}</sup>)"
                respuesta = f"{coef}x^{nuevo_n}"
                
        elif caso == 'exponencial':
            a = random.randint(2, 5)
            pregunta = f"d/dx ({a}e<sup>x</sup>)"
            respuesta = f"{a}e^x"
            
        elif caso == 'trigonometrica':
            func = random.choice(['sin', 'cos'])
            if func == 'sin':
                pregunta = "d/dx (sin(x))"
                respuesta = "cos(x)"
            else:
                pregunta = "d/dx (cos(x))"
                respuesta = "-sin(x)"
                
        else: # logaritmica
            pregunta = "d/dx (ln(x))"
            respuesta = "1/x"
            
        return pregunta, respuesta, f"derivadas_{caso}"

    # INTEGRALES (Basicas)
    if tipo == 'integrales':
        caso = random.choice(['polinomio', 'exponencial', 'trigonometrica'])
        
        if caso == 'polinomio':
            n = random.randint(1, 3)
            nuevo_n = n + 1
            denominador = nuevo_n
            pregunta = f"∫ x<sup>{n}</sup> dx"
            respuesta = f"1/{denominador}x^{nuevo_n}"
            
        elif caso == 'exponencial':
            pregunta = "∫ e<sup>x</sup> dx"
            respuesta = "e^x"
            
        else: # trigonometrica
            func = random.choice(['sin', 'cos'])
            if func == 'sin':
                pregunta = "∫ sin(x) dx"
                respuesta = "-cos(x)"
            else:
                pregunta = "∫ cos(x) dx"
                respuesta = "sin(x)"
                
        return pregunta, respuesta, f"integrales_{caso}"

    # L'HOPITAL
    if tipo == 'l_hopital':
        caso = random.choice(['sen_sobre_x', 'exp_menos_1'])
        
        if caso == 'sen_sobre_x':
            a = random.randint(2, 5)
            pregunta = f"lim (x -> 0) [sin({a}x) / x]"
            respuesta = str(a)
        else:
            a = random.randint(2, 5)
            pregunta = f"lim (x -> 0) [(e<sup>{a}x</sup> - 1) / x]"
            respuesta = str(a)
            
        return pregunta, respuesta, f"l_hopital_{caso}"

    # PROBLEMAS DE OPTIMIZACION
    if tipo == 'optimizacion':
        caso = random.choice(['area_maxima', 'cerca_rectangular'])
        
        if caso == 'area_maxima':
            perimetro = random.choice([40, 60, 80, 100])
            lado = perimetro // 4
            area_max = lado ** 2
            pregunta = f"Area maxima de un rectangulo con perimetro {perimetro}m"
            respuesta = str(area_max)
        else:
            suma = random.choice([20, 30, 50])
            mitad = suma / 2
            prod_max = int(mitad * mitad)
            pregunta = f"Producto maximo de dos numeros positivos cuya suma es {suma}"
            respuesta = str(prod_max)
            
        return pregunta, respuesta, f"optimizacion_{caso}"

    # INTEGRACION POR PARTES
    if tipo == 'integrales_partes':
        a = random.randint(1, 3)
        if a == 1:
            pregunta = "∫ x · e<sup>x</sup> dx"
            respuesta = "(x - 1)e^x"
        else:
            pregunta = f"∫ x · e<sup>{a}x</sup> dx"
            respuesta = f"(1/{a}x - 1/{a**2})e^{a}x"
            
        return pregunta, respuesta, "integrales_partes"

    # SUSTITUCION TRIGONOMETRICA

    if tipo == 'sustitucion_trig':
        a = random.choice([2, 3, 4, 5])
        a2 = a ** 2
        pregunta = f"∫ (1 / √({a2} - x<sup>2</sup>)) dx"
        respuesta = f"arcsin(x/{a})"
        
        return pregunta, respuesta, "sustitucion_trig"

    # FRACCIONES PARCIALES
    if tipo == 'fracciones_parciales':
        a = random.randint(1, 3)
        b = a + random.randint(1, 3)
        pregunta = f"∫ [1 / ((x - {a})(x - {b}))] dx"
        resta_ab = b - a
        respuesta = f"1/{resta_ab} ln((x-{b})/(x-{a}))"
        
        return pregunta, respuesta, "fracciones_parciales"

    return "Error", 0, "desconocido"