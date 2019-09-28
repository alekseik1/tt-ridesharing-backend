def init_mysql_driver():
    # Workaround about mysql driver (since mysql-python doesn't work)
    # see https://toster.ru/q/74604 for details
    import pymysql
    pymysql.install_as_MySQLdb()
