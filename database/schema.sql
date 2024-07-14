CREATE TABLE IF NOT EXISTS warns (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(30) NOT NULL,
  server_id VARCHAR(30) NOT NULL,
  moderator_id VARCHAR(30) NOT NULL,
  reason VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS verification_codes (
  discord_id VARCHAR(30) PRIMARY KEY,
  roblox_id VARCHAR(30) NOT NULL,
  code VARCHAR(100) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS verifications (
  id SERIAL PRIMARY KEY,
  discord_id VARCHAR(30) NOT NULL,
  roblox_id VARCHAR(30) NOT NULL,
  verified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tracked_users (
  roblox_id VARCHAR(30) PRIMARY KEY,
  posted BOOLEAN NOT NULL,
  moderator_id VARCHAR(30) NOT NULL,
  reason TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)