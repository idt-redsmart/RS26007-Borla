#!/bin/bash
# router_socket_permissions.sh
# ----------------------------
# Rende il socket dell'arduino-router (/run/arduino-router.sock) accessibile
# all'app Borla, che gira come utente normale (arduino) e non come root.
#
# Problema: l'arduino-router ricrea il socket a ogni avvio e quando App Lab
# carica uno sketch; i permessi tornano quelli originali e l'app resta ferma su
# "Load cell not ready ... [PermissionError: [Errno 13] Permission denied]".
#
# Soluzione: un'unità systemd .path sorveglia il socket e, ogni volta che viene
# creato o i suoi permessi cambiano, avvia un servizio che aggiunge lettura e
# scrittura per tutti gli utenti (chmod a+rw). I permessi esistenti non vengono
# mai tolti, quindi gli altri programmi che usano il router non sono toccati.
#
# Uso (sulla scheda, una volta sola):
#   sudo bash tools/router_socket_permissions.sh              installa e applica subito
#   sudo bash tools/router_socket_permissions.sh --uninstall  rimuove tutto
#
# Verifica:  ls -l /run/arduino-router.sock   →  srw-rw-rw-
# Log:       journalctl -u borla-router-perms

set -eu

NAME=borla-router-perms
HELPER=/usr/local/sbin/$NAME.sh
SERVICE=/etc/systemd/system/$NAME.service
PATH_UNIT=/etc/systemd/system/$NAME.path

# /var/run è un collegamento a /run: systemd vuole il percorso reale
RUNDIR="$(readlink -f /var/run 2>/dev/null)" || RUNDIR=/run
SOCK="$RUNDIR/arduino-router.sock"

if [ "$(id -u)" -ne 0 ]; then
    echo "Serve root: sudo bash $0" >&2
    exit 1
fi

if [ "${1:-}" = "--uninstall" ]; then
    systemctl disable --now "$NAME.path" 2>/dev/null || true
    systemctl disable "$NAME.service" 2>/dev/null || true
    rm -f "$HELPER" "$SERVICE" "$PATH_UNIT"
    systemctl daemon-reload
    echo "Rimosso. Il socket torna ai permessi originali al prossimo riavvio dell'arduino-router."
    exit 0
fi

# ── Script che sistema i permessi ─────────────────────────────────────────────
cat > "$HELPER" <<EOF
#!/bin/sh
# Generato da router_socket_permissions.sh (app Borla).
# Aggiunge lettura/scrittura per tutti al socket dell'arduino-router.
# Se i permessi sono già giusti non fa nulla: il chmod cambierebbe di nuovo il
# socket e riattiverebbe l'unità .path all'infinito.
SOCK="$SOCK"

[ -S "\$SOCK" ] || exit 0

MODE=\$(stat -c %a "\$SOCK")
[ \$(( 0\$MODE & 06 )) -eq 6 ] && exit 0

chmod a+rw "\$SOCK"
echo "\$SOCK: permessi da \$MODE a \$(stat -c %a "\$SOCK")"
EOF
chmod 755 "$HELPER"

# ── Servizio: esegue lo script (all'avvio e quando lo chiede l'unità .path) ───
cat > "$SERVICE" <<EOF
[Unit]
Description=Permessi del socket arduino-router per l'app Borla
After=arduino-router.service

[Service]
Type=oneshot
ExecStart=$HELPER

[Install]
WantedBy=multi-user.target
EOF

# ── Sorveglianza: socket ricreato o permessi cambiati → servizio ──────────────
cat > "$PATH_UNIT" <<EOF
[Unit]
Description=Sorveglia il socket arduino-router per l'app Borla

[Path]
PathChanged=$SOCK
Unit=$NAME.service

[Install]
WantedBy=paths.target
EOF

systemctl daemon-reload
systemctl enable --now "$NAME.path"
systemctl enable "$NAME.service"
systemctl start "$NAME.service"         # sistema subito il socket attuale

echo
echo "Installato. Stato attuale del socket:"
if [ -S "$SOCK" ]; then
    ls -l "$SOCK"
else
    echo "  $SOCK non esiste ancora: verrà sistemato appena l'arduino-router lo crea."
fi
echo
echo "Unità systemd che riguardano l'arduino-router (per controllo):"
systemctl list-unit-files 2>/dev/null | grep -i 'arduino-router' || echo "  nessuna con questo nome"
