# -*- coding: UTF-8 -*-
import sys
if __name__ == "__main__":
    sys.path.append("..")
    from find_password import send_reset_mail, send_registry_mail, send_bind_mail
    send_reset_mail("459545754@qq.com","监控类12","asdfffffffffffff")
    send_registry_mail("459545754@qq.com","健康的23","qwerrrrrrrrrr")
    send_bind_mail("459545754@qq.com", "监控类12", "http://www.校园星空.com")
