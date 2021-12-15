# JMS_user_handler
针对JumpServer2.2.2，在后台通过快速命令行实现新用户添加、已有用户查询与删除。
针对用户删除操作，仍存在外键关联时发生的错误。

# 用法
1. 需要提前申请三个模板用户（每个角色各一个），接着填写配置文件config.yaml，值得注意的是堡垒机所在的服务器的mysql，根用户可能是空密码
2. 增加pyMySQL库
```
/opt/py3/bin/pip install pymysql
```

3. 添加用户
```
/opt/py3/bin/python main.py --action=create --role=admin --username=new_admin
```

4. 查询用户
```
/opt/py3/bin/python main.py --action=find --id=account_id
```

5. 删除用户
```
/opt/py3/bin/python main.py --action=delete --id=account_id
```
