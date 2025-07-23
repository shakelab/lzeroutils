# Copia il file nella directory di systemd
sudo cp lzeroserver.service /etc/systemd/system/

# Ricarica systemd per includere la nuova unit
sudo systemctl daemon-reload

# Abilita avvio automatico al boot
sudo systemctl enable lzeroserver

# Avvia il servizio
sudo systemctl start lzeroserver

# Controlla status
sudo systemctl status lzeroserver

# Log in tempo reale
journalctl -u lzeroserver -f
