# coding: utf-8
import demo.core.config as cf
from demo.core.config.config import DBConfig
import demo.core.db as db


def init_env():
    cf.set_up()

    db_config: DBConfig = cf.get_config().db
    db.set_up(
        db_config.build_dsn(),
        pool_size=db_config.pool_size,
        max_overflow=db_config.max_overflow,
        pool_recycle=db_config.max_overflow,
    )
