# LP3 manager

LP3 manager is a python project for [nearcrowd lp3](https://nearcrowd.com/lp3).
* It helps to manage users' permissions. Because one user can have multiple accounts connected to him.
* Adds interaction through telegram.

## Usage
**Firstly set up [environment variables](#environment-variables).**
* Start the project: `docker compose up --build -d`
* Run script from `scripts/` folder: `bash run_script.sh {name}`
* Create backup: `bash create_backup.sh`

## Environment variables
Environment files supposed to be in `env/` folder
1) `account.env` - configuration for access to nearcrowd:
    * `account_id` - your near wallet.
    * `private_key` - your private key **with access to nearcrowd**.
    * `farm_id` - farm id.
2) `bot.env` - configuration for telegram bot ([telethon library](https://github.com/LonamiWebs/Telethon)):
    * `BOT_NAME` - bot's name.
    * `TOKEN` - bot's token from @BotFather.
    * `API_ID` - your [API ID](https://my.telegram.org).
    * `API_HASh` - your [API HASH](https://my.telegram.org).
3) `database.env` - configuration for [postgres](https://hub.docker.com/_/postgres):
    * `POSTGRES_USER` - username for database.
    * `POSTGRES_PASSWORD` - password for database.
    * `POSTGRES_DB` - database name.
    * `POSTGRES_HOST` - should be the same as service name in `docker-compose.yml`.
4) `watcher.env` - configuration for watcher
    * `watched_account` - account that is used for payments
    * `review_prcie` - price for 1 review in **micro** nears

## Services structure
Services are described in `docker-compose.yml`.
1) `scraper` (`log_scraper/`) - scraps logs from nearcrowd.
2) `permissions` (`review_permissions/`) - automatically adjusts users' permissions (only review allowance for now) on nearcrowd to stay in sync with local ones.
3) `bot` (`bot/`) - telegram bot.
4) `sampler` (`sampler/`) - automatically takes a sample periodically.
5) `watcher` (`watcher/`) - watches payments for reviews
6) `tester` (no folder) - is used for testing inside container, mainly for running scripts.
