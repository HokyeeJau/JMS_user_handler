#!/opt/py3/bin/python
# @author: Hokyee Jau
# @date: 2021/12/10


import os
import time
import uuid
import yaml
import logging
import pymysql
import argparse

from pathlib import Path


def get_cols(conn):
    """ 获取数据库列名

    :param conn: 数据库连接对象
    :return: 表列名列表
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users_user")
    cols = cursor.description

    col_list = []
    for col in cols:
        col_list.append(col[0])
    return col_list


def fetch_mappings(cursor):
    """ 获取单条数据的映射关系

    :param cursor: 已经运行了命令行的cursor
    :return: dict，键值对数据
    """
    cols = cursor.description
    row = cursor.fetchone()
    mappings = {}
    for i in range(len(cols)):
        col = cols[i][0]
        mappings[col] = row[i]

    return mappings


def add_account(conn, role: str, username: str, temp: dict):
    """ 添加新的账户

    :param username:
    :param cursor:
    :param role:
    :return:
    """

    if role == 'admin':
        sql = add_sql(username, temp['admin'])
    elif role == 'auditor':
        sql = add_sql(username, temp['auditor'])
    elif role == 'user':
        sql = add_sql(username, temp['user'])
    else:
        logger.error("角色不存在或角色名错误！")
        conn.close()
        exit(1)
    print(sql)
    logger.info(f"添加命令行为：{sql}")
    cursor = conn.cursor()
    cursor.execute(sql)
    logger.info(f"添加{username}运行成功！")
    cursor.close()


def _add_sql_temp(cols: str, values: str):
    return f"INSERT INTO users_user({pymysql.escape_string(cols)}) VALUES({values})"


def add_sql(username: str, temp: dict):
    """ 添加新的管理员

    :param username: 用户名
    :param temp: 角色模板数据
    :return:
    """
    keys = []
    values = []

    id = uuid.uuid4().__str__()[:ID_LEN].replace('-', '0')
    while id in ids:
        id = uuid.uuid4().__str__()[:ID_LEN].replace('-', '0')

    print(id)
    # 更改基础信息
    temp['id'] = id
    temp['email'] = f"{id[6:12]}@aiit.com"
    temp['name'] = username
    temp['username'] = username
    temp['created_by'] = 'Administrator'

    # 更改时间信息
    cur = time.time()
    date_joined = time.strftime('%Y-%m-%d %X', time.localtime(cur))
    expired = time.strftime('%Y-%m-%d %X', time.localtime(cur+100*24*60*60))
    date_password_last_update = time.strftime('%Y-%m-%d %X', time.localtime(cur+2))
    last_login = time.strftime('%Y-%m-%d %X', time.localtime(cur+10))
    temp['date_joined'] = date_joined
    temp['date_expired'] = expired
    temp['last_login'] = last_login
    temp['date_password_last_updated'] = date_password_last_update

    for k, v in temp.items():
        if v is None:
            temp[k] = ''

    # 将键值对拆分成可写入数据库的样式
    for k, v in temp.items():
        keys.append(k)
        if not isinstance(v, str):
            values.append("'"+str(v)+"'")
        else:
            values.append("'"+v+"'")

    sql = _add_sql_temp(','.join(keys), ','.join(values))
    return sql


def cache_ids(conn):
    """ 预加载所有的账户id

    :param conn: 数据库连接对象
    :return: 账户id列表
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users_user")
    rows = cursor.fetchall()

    ids = []
    for tpl in rows:
        ids.append(tpl[0])

    cursor.close()
    return ids


def find_account(conn, id: str) -> dict:
    """ 查询账户

    :param id: 账户id
    :return: 返回键值对
    """
    if id not in ids:
        logger.warning(f"{id}不在数据库内！")
        return {}

    sql = f"SELECT * FROM users_user where id = '{pymysql.escape_string(id)}'"
    logger.info(f"查询命令行为：{sql}")
    cursor = conn.cursor()
    cursor.execute(sql)

    mappings = fetch_mappings(cursor)

    cursor.close()
    logger.info(f"已找到{args.id}!")
    logger.info(mappings)


def delete_account(conn, id: str):
    """ 删除账户

    :param id: 账户id
    """
    print(ids)
    if id in ids:
        sql = f"DELETE FROM users_user where id = '{pymysql.escape_string(id)}'"
        logger.info(f"删除命令行为：{sql}")
        cursor = conn.cursor()
        cursor.execute(sql)

        logger.info(f"删除{id}成功！")
        cursor.close()
    else:
        logger.warning("该id号不存在！")


def get_template_data(conn, template_username):
    name = pymysql.escape_string(template_username)
    sql = f"SELECT * FROM users_user where username='{name}'"
    cursor = conn.cursor()
    cursor.execute(sql)

    mappings = fetch_mappings(cursor)

    cursor.close()
    return mappings


""" 日志打印器 """
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

rq = 'test'
t = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))

log_name = os.path.join('.', rq + '.log')
fh = logging.FileHandler(log_name, mode='a+')
fh.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s-%(filename)s[line:%(lineno)d][%(levelname)s]: %(message)s")
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.info(f"{t}: 开始记录新操作")


""" 命令参数解析器 """
parser = argparse.ArgumentParser(description='JMS快捷账户管理器')
parser.add_argument("--action", help="操作(delete, create, find)，增加操作请添加账户角色与角色名称，"
                                     "删除与查询请输入账户id")
parser.add_argument("--role", help='账户角色(admin, auditor, user)')
parser.add_argument("--username", help="添加的角色名称")
parser.add_argument("--id", help="账户id，仅用作查询与删除")
args = parser.parse_args()
logger.info("命令行参数：" + str(args.__dict__))


""" 命令行检查 """
if args.action:
    if args.action not in ['delete', 'create', 'find']:
        logger.error("动作错误：只有delete, create, find.")
        exit(1)

if args.action == 'create' and not args.role:
    logger.warning("变量缺失：缺少角色，默认为普通用户")
    args.__setattr__('role', 'user')

if args.action == 'create' and not args.username:
    logger.error("变量缺失：必须输入添加的账户名")
    exit(1)

if args.action in ['delete', 'find'] and not args.id:
    logger.error("变量缺失：必须输入查询或者删除的账户id")
    exit(1)


""" 连接数据库 """
config_dir = os.path.dirname(__file__)
config_path = os.path.join(config_dir, 'config.yaml')

with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.load(f.read(), Loader=yaml.FullLoader)

db_config = config['db']

check_keys = {'host', 'user', 'passwd', 'db', 'port'}
if (db_config.keys()) < check_keys:
    logger.error("数据库配置变量缺失，请检查是否存在ip, user, password, name, port。")
    exit(1)


db_config['port'] = int(db_config['port'])
if isinstance(db_config['passwd'], int):
    db_config['passwd'] = str(db_config['passwd'])
elif not db_config['passwd']:
    db_config['passwd'] = ''
# conf['charset'] = 'urf8'


try:
    conn = pymysql.connect(**db_config)
except Exception as e:
    logger.error("数据库连接失败！")
    logger.error(e.__repr__())
    exit(1)


""" 预加载id """
ids = cache_ids(conn)
ID_LEN = len(ids[0])

""" 运行 """
try:
    if args.action == 'create':
        # 获取每个模板角色的用户名
        try:
            admin = config['template']['admin']
            auditor = config['template']['auditor']
            user = config['template']['user']
        except Exception as e:
            logger.error("数据库模板导入失败！")
            logger.error(e.__repr__())
            conn.close()
            exit(1)

        # 提取三个角色的模板数据
        try:
            temp = {}
            temp['admin'] = get_template_data(conn, admin)
            temp['auditor'] = get_template_data(conn, auditor)
            temp['user'] = get_template_data(conn, user)
        except Exception as e:
            logger.error("数据库读取失败！")
            logger.error(e.__repr__())
            conn.close()
            exit(1)
        # 运行添加命令
        add_account(conn, args.role, args.username, temp)
    elif args.action == 'find':
        find_account(conn, args.id)
    elif args.action =='delete' :
        delete_account(conn, args.id)

    conn.commit()
except Exception as e:
    logger.error("操作失败！")
    logger.error(e.__repr__())
    conn.rollback()
    conn.close()
    exit(1)


conn.close()
