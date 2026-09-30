#!/bin/bash
# Recorre TODO el contrato contra un servidor, incluidos los caminos de error.
#   bash smoke.sh                      -> http://127.0.0.1:8000/api
#   CODIGO_PROFESOR=... bash smoke.sh https://otro-servidor/api
# Sin acentos en los cuerpos: Git Bash en Windows los manda en cp1252 y el servidor responde 400.
# Cada línea imprime el código HTTP esperado entre corchetes; compáralo con el real.
B=${1:-http://127.0.0.1:8000/api}
# El código de profesor sale del entorno o, si no está, del .env: el mismo que usa tu servidor.
[ -z "$CODIGO_PROFESOR" ] && [ -f .env ] && CODIGO_PROFESOR=$(grep -E '^CODIGO_PROFESOR=' .env | cut -d= -f2- | tr -d '\r')
U="smoke.$(date +%s)"
j() { curl -s -w ' [%{http_code}]' "$@"; echo; }
tok() { grep -oE "\"$1\": ?\"[^\"]+" | cut -d'"' -f4; }

echo "== 1 register alumno (201)";        j -X POST $B/auth/register -H 'Content-Type: application/json' -d "{\"usuario\":\"$U\",\"password\":\"secreta123\"}" | tee r.json | tail -c 120
echo "== 2 register repetido (409)";      j -X POST $B/auth/register -H 'Content-Type: application/json' -d "{\"usuario\":\"$U\",\"password\":\"secreta123\"}"
echo "== 3 password corta (422)";         j -X POST $B/auth/register -H 'Content-Type: application/json' -d '{"usuario":"otro.smoke","password":"corta"}'
echo "== 4 rol en el body se ignora (201, alumno)"; j -X POST $B/auth/register -H 'Content-Type: application/json' -d "{\"usuario\":\"$U.tramposo\",\"password\":\"secreta123\",\"rol\":\"profesor\",\"codigoProfesor\":\"nope\"}" | grep -oE '"rol": ?"[a-z]+"| \[[0-9]+\]' | tr '\n' ' '; echo
echo "== 5 login mal (401)";              j -X POST $B/auth/login -H 'Content-Type: application/json' -d "{\"usuario\":\"$U\",\"password\":\"otra\"}"
echo "== 6 login bien (200)";             j -X POST $B/auth/login -H 'Content-Type: application/json' -d "{\"usuario\":\"$U\",\"password\":\"secreta123\"}" > l.json; tail -c 60 l.json; echo
AT=$(tok accessToken < l.json); RT=$(tok refreshToken < l.json)
echo "== 7 avisos sin token (401)";       j $B/avisos
echo "== 8 avisos con token (200)";       j -H "Authorization: Bearer $AT" $B/avisos | tail -c 80
echo "== 9 me (200)";                     j -H "Authorization: Bearer $AT" $B/auth/me
echo "== 10 alumno publica (403)";        j -X POST $B/avisos -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' -d '{"titulo":"Hola","cuerpo":"Esto no debe pasar nunca"}'
echo "== 11 register profesor (201)";     j -X POST $B/auth/register -H 'Content-Type: application/json' -d "{\"usuario\":\"$U.prof\",\"password\":\"profesor123\",\"codigoProfesor\":\"${CODIGO_PROFESOR}\"}" > p.json; grep -oE '"rol": ?"[a-z]+"' p.json; tail -c 8 p.json; echo
PT=$(tok accessToken < p.json)
echo "== 12 profesor publica (201)";      j -X POST $B/avisos -H "Authorization: Bearer $PT" -H 'Content-Type: application/json' -d '{"titulo":"Examen parcial","cuerpo":"El parcial es el jueves a las 10:00 en el salon de siempre."}' > a.json; tail -c 100 a.json; echo
AID=$(grep -oE '"id": ?[0-9]+' a.json | head -1 | grep -oE '[0-9]+')
echo "== 13 aviso invalido (422)";        j -X POST $B/avisos -H "Authorization: Bearer $PT" -H 'Content-Type: application/json' -d '{"titulo":"Ok","cuerpo":"corto"}'
echo "== 14 refresh (200)";               j -X POST $B/auth/refresh -H 'Content-Type: application/json' -d "{\"refreshToken\":\"$RT\"}" > rf.json; tail -c 60 rf.json; echo
RT2=$(tok refreshToken < rf.json)
echo "== 15 reusar refresh viejo (401)";  j -X POST $B/auth/refresh -H 'Content-Type: application/json' -d "{\"refreshToken\":\"$RT\"}"
echo "== 16 logout (revoked 1)";          j -X POST $B/auth/logout -H 'Content-Type: application/json' -d "{\"refreshToken\":\"$RT2\"}"
echo "== 17 token alterado (401)";        H=$(echo $AT | cut -d. -f1); S=$(echo $AT | cut -d. -f3); P2=$(printf '{"sub":"%s","rol":"profesor","iat":1,"exp":9999999999}' "$U" | base64 -w0 | tr '+/' '-_' | tr -d '='); j -X POST $B/avisos -H "Authorization: Bearer $H.$P2.$S" -H 'Content-Type: application/json' -d '{"titulo":"Hackeo","cuerpo":"Cambie mi rol en el cliente jeje"}'
echo "== 18 borrar aviso (204)";          j -X DELETE -H "Authorization: Bearer $PT" $B/avisos/$AID
echo "== 19 borrar inexistente (404)";    j -X DELETE -H "Authorization: Bearer $PT" $B/avisos/$AID
echo "== 20 cerrar todas (200)";          j -X DELETE -H "Authorization: Bearer $PT" $B/auth/sesiones
rm -f r.json l.json p.json a.json rf.json
