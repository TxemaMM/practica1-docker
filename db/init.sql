CREATE TABLE IF NOT EXISTS games (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(60) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS votes (
    id         SERIAL PRIMARY KEY,
    game_id    INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO games (name) VALUES
    ('The Legend of Zelda: Breath of the Wild'),
    ('Hollow Knight'),
    ('Ark Survival Evolved'),
    ('Elden Ring'),
    ('Minecraft'),
    ('Stardew Valley'),
    ('Portal 2'),
    ('The Witcher 3: Wild Hunt'),
    ('Hades'),
    ('Red Dead Redemption 2')
ON CONFLICT (name) DO NOTHING;