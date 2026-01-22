### MySQL Datenbank

#### Schritt 1 (ENV):

- `.env.example` nach `.env` kopieren
- Korrekte Werte eintragen (DB-Name, Passwort, Port, etc.)

#### Schritt 2 (Docker):

- Container starten: `docker compose up -d`
- Status prüfen: `docker compose ps`

#### Schritt 3 (MySQL):

- Datenbankverbindung herstellen
- Datenbank-Skript ausfühlen: `init.sql`
