% =============================================================================
% MOTOR EXPERTO: REGLAS ORTOGRÁFICAS RAE (ANSI/ASCII)
% =============================================================================

% -----------------------------------------------------------------------------
% 1. REGLA DE LA H
% Determina si el error ortográfico radica en la omisión o adición incorrecta de la letra 'h'.
% Parámetros:
%   O: Palabra Original (con error)
%   C: Palabra Corregida
%   Tercer argumento: Nombre/Categoría de la regla deducida ('Uso de la H')
%   Cuarto argumento: Explicación teórica de la norma
% -----------------------------------------------------------------------------
clasificar_regla(O, C, 'Uso de la H', 'Formas del verbo haber o voces con hache etimologica que no representan fonema.') :-
    % Caso 1: La palabra original NO contiene 'h' (\+ es negación), pero la corregida SÍ contiene 'h' (omisión de 'h')
    (\+ sub_atom(O, _, _, _, 'h'), sub_atom(C, _, _, _, 'h')) ;
    % Operador ';' representa una disyunción lógica (OR / O)
    % Caso 2: La palabra original SÍ contiene 'h', pero la corregida NO contiene 'h' ('h' sobrante o espuria)
    (sub_atom(O, _, _, _, 'h'), \+ sub_atom(C, _, _, _, 'h')).

% -----------------------------------------------------------------------------
% 2. REGLA DE B / V
% Detecta la confusión gráfica entre las consonantes bilabial 'b' y labiodental 'v'.
% -----------------------------------------------------------------------------
clasificar_regla(O, C, 'Grafia B / V', 'Confusion entre labiales. Se rige por raices lexicas, prefijos bi-/bis- o desinencias en -aba.') :-
    % Caso 1: La palabra original fue escrita con 'b' y la corrección lleva 'v'
    (sub_atom(O, _, _, _, 'b'), sub_atom(C, _, _, _, 'v')) ;
    % Caso 2: La palabra original fue escrita con 'v' y la corrección lleva 'b'
    (sub_atom(O, _, _, _, 'v'), sub_atom(C, _, _, _, 'b')).

% -----------------------------------------------------------------------------
% 3. REGLA DE C / S / Z
% Identifica errores de intercambio entre sibilantes (seseo, ceceo o confusión de grafías).
% -----------------------------------------------------------------------------
clasificar_regla(O, C, 'Grafia C / S / Z', 'Diferenciacion de sibilantes ante vocales E, I (uso de C frente a S) o terminaciones en -azo/-ces.') :-
    % Caso 1: El original tiene 's' y la palabra correcta tiene 'c' o 'z'
    (sub_atom(O, _, _, _, 's'), (sub_atom(C, _, _, _, 'c') ; sub_atom(C, _, _, _, 'z'))) ;
    % Caso 2: El original tiene 'c' y la palabra correcta tiene 's' o 'z'
    (sub_atom(O, _, _, _, 'c'), (sub_atom(C, _, _, _, 's') ; sub_atom(C, _, _, _, 'z'))) ;
    % Caso 3: El original tiene 'z' y la palabra correcta tiene 's' o 'c'
    (sub_atom(O, _, _, _, 'z'), (sub_atom(C, _, _, _, 's') ; sub_atom(C, _, _, _, 'c'))).

% -----------------------------------------------------------------------------
% 4. REGLA DE G / J
% Clasifica errores relacionados con el fonema velar fricativo sordo (/x/) escrito con 'g' o 'j'.
% También contempla el uso erróneo de 'h' por 'j' (fonética aspirada coloquial).
% -----------------------------------------------------------------------------
clasificar_regla(O, C, 'Grafia G / J', 'El sonido velar sordo se escribe con J ante cualquier vocal o con G ante E, I segun la raiz.') :-
    % Caso 1: El usuario escribió con 'h' muda/aspirada una palabra que lleva 'j' (ej. 'mehorar' -> 'mejorar')
    (sub_atom(O, _, _, _, 'h'), sub_atom(C, _, _, _, 'j')) ;
    % Caso 2: Se usó 'j' en lugar de 'g'
    (sub_atom(O, _, _, _, 'j'), sub_atom(C, _, _, _, 'g')) ;
    % Caso 3: Se usó 'g' en lugar de 'j'
    (sub_atom(O, _, _, _, 'g'), sub_atom(C, _, _, _, 'j')).

% -----------------------------------------------------------------------------
% 5. REGLA DE PALABRAS PEGADAS / LOCUCIONES
% Detecta cuando dos o más palabras se escribieron unidas indebidamente (ej. 'yaque' -> 'ya que').
% -----------------------------------------------------------------------------
clasificar_regla(O, C, 'Separacion de palabras', 'Union indebida de conjunciones, preposiciones o locuciones que deben escribirse por separado.') :-
    % El texto original NO contiene ningún carácter de espacio en blanco
    \+ sub_atom(O, _, _, _, ' '),
    % El texto corregido SÍ contiene al menos un espacio en blanco
    sub_atom(C, _, _, _, ' ').

% -----------------------------------------------------------------------------
% 6. REGLA DE ACENTUACIÓN
% Detecta la falta de tilde ortográfica en la palabra ingresada.
% -----------------------------------------------------------------------------
clasificar_regla(O, C, 'Acentuacion (Tilde)', 'Omision de la tilde en vocal tonica obligatoria por norma de agudas, graves, esdrujulas o hiato.') :-
    % La palabra original NO posee ninguna vocal con tilde
    \+ tiene_acento(O),
    % La palabra corregida SÍ posee al menos una vocal acentuada
    tiene_acento(C).

% Predicado auxiliar: verifica si la palabra 'P' contiene alguna vocal con tilde
tiene_acento(P) :-
    % Evalúa si dentro del átomo 'P' existe alguna de las vocales tildadas (á, é, í, ó, ú)
    sub_atom(P, _, _, _, 'á') ; sub_atom(P, _, _, _, 'é') ;
    sub_atom(P, _, _, _, 'í') ; sub_atom(P, _, _, _, 'ó') ;
    sub_atom(P, _, _, _, 'ú').

% -----------------------------------------------------------------------------
% 7. REGLA POR DEFECTO (FALLBACK / COMODÍN)
% Se ejecuta si ninguna de las reglas anteriores coincidió con el error analizado.
% Las variables anónimas '_' indican que acepta cualquier valor para O y C.
% -----------------------------------------------------------------------------
clasificar_regla(_, _, 'Correccion lexica RAE', 'Ajuste morfosintactico conforme a la norma academica de la lengua espanola.').