from __future__ import annotations
from dataclasses import dataclass, asdict,fields
from ldap3 import Server, Connection, ALL, MODIFY_REPLACE, SUBTREE
from typing import Any
import inspect
from datetime import datetime
from ldap3.utils.hashed import hashed
from passlib.hash import ldap_salted_sha1

__all__ = ['LdapConfig', 'inetOrgPerson', 'posixAccount', 'LDAP_OP']

@dataclass
class LdapConfig:
    HOST: str = "openldap"
    PORT: int = 389
    BASE_DN: str = None
    BIND_PW: str = None
    BIND_DN: str = None
    USER_BASE_RDN: str = None
    GROUP_BASE_RDN: str = None
    USER_FILTER: str = '(cn=*)'
    GROUP_FILTER: str = '(cn=*)'
    TLS = False

    @property
    def SERVER_URL(self) -> str:
        if self.HOST is None:
            raise ValueError("HOST is None")
        return '{PROTO}://{HOST}:{PORT}'.format(
            PROTO='ldaps' if self.TLS else 'ldap',
            HOST=self.HOST,
            PORT=self.PORT)

    @property
    def USER_BASE_DN(self) -> str:
        if self.USER_BASE_RDN is None or self.USER_BASE_RDN.strip() == '':
            return self.BASE_DN
        return '{RDN},{BASE}'.format(RDN=self.USER_BASE_RDN, BASE=self.BASE_DN)

    @property
    def GROUP_BASE_DN(self) -> str:
        if self.GROUP_BASE_RDN is None or self.GROUP_BASE_RDN.strip() == '':
            return self.BASE_DN
        return '{RDN},{BASE}'.format(RDN=self.GROUP_BASE_RDN, BASE=self.BASE_DN)

    def server(self) -> Server:
        return Server(host=self.HOST, port=self.PORT, use_ssl=self.TLS, get_info=ALL)

    def connect(self) -> Connection:
        if self.BIND_DN is None:
            raise ValueError("BIND_DN is None")
        elif self.BIND_PW is None:
            raise ValueError("BIND_PW is None")
        server = self.server()
        return Connection(server, self.BIND_DN, self.BIND_PW, auto_bind=True)


@dataclass
class inetOrgPerson:
    uid: str
    sn: str
    givenName: str
    mail: str = None
    telephoneNumber: str = None
    title: str = None
    description: str = None
    userPassword: str = None
    departNumber: int = None

    def asdict(self) -> dict[str, Any]:
        out_put = asdict(self)
        out_put['cn'] = '{GIVEN_NAME} {SN}'.format(GIVEN_NAME=self.givenName,SN=self.sn)
        return out_put

    def copy_from(self,other:inetOrgPerson):
        field_names = self.__dict__.keys()
        for key, value in other.asdict().items():
            if key in field_names:
                self.__dict__[key] = value

@dataclass
class posixAccount(inetOrgPerson):
    homeDirectory: str = '/home'
    loginShell: str = '/bin/bash'
    uidNumber: int = None
    gidNumber: int = 500
    


class LDAP_OP:

    def __init__(self, ldap_config: LdapConfig = None, is_log: bool = False) -> None:
        self.__server: Server = None
        self.__conn: Connection = None
        self.__conn_status = False
        if ldap_config is not None and (LdapConfig, ldap_config):
            self.ldap_config = ldap_config
        else:
            self.__ldap_config = LdapConfig()
        self.is_log: bool = is_log

    @property
    def ldap_config(self) -> LdapConfig:
        return self.__ldap_config

    @ldap_config.setter
    def ldap_config(self, ldap_config: LdapConfig):
        if issubclass(type(ldap_config), LdapConfig):
            self.__ldap_config = ldap_config
            self.connect()
        else:
            raise ValueError("ldap_config must be a LdapConfig type")

    @property
    def conn(self) -> Connection:
        return self.__conn

    @property
    def server(self) -> Server:
        return self.__server

    @property
    def conn_status(self) -> bool:
        return self.__conn_status

    def get_next_uid_number(self) -> int:
        if not self.check_conn():
            return -1
        search_filter = '(objectClass=inetOrgPerson)'

        if self.conn.search(self.ldap_config.USER_BASE_DN, search_filter, search_scope=SUBTREE, attributes=['uidNumber']):
            uid_list = [int(entry['uidNumber'].value)
                        for entry in self.conn.entries]
            return max(uid_list)+1
        return int(self.check_error())-1

    def add(self, DN: str, object_class: list[str], attributes: dict[str, Any]) -> bool:
        if not self.check_conn():
            return False
        if self.conn.add(DN, object_class, attributes):
            return True
        return self.check_error()

    def midify(self, dn: str, changes: dict[str, Any]) -> bool:
        if not self.check_conn():
            return False
        new_changes = {}
        for key, value in changes.items():
            new_changes[key] = [(MODIFY_REPLACE, value)]
        if self.conn.modify(dn, new_changes):
            return True
        return self.check_error()
    # changes = {'telephoneNumber': [(MODIFY_REPLACE, ['555-5678'])]}

    def del_dn(self, dn: str) -> bool:
        if not self.check_conn():
            return False
        if self.conn.delete(dn):
            return True
        return self.check_error()

    def copy(self, source_dn: str, target_dn: str) -> bool:
        if not self.check_conn():
            return False
        if not self.conn.search(source_dn, '(objectClass=*)', attributes=['*']):
            return self.check_error()
        source_entry = self.conn.entries[0]
        # read source entry
        attributes = {}
        for attr in source_entry:
            attributes[attr.key] = attr.value
        attributes.pop('dn')
        object_class = attributes['objectClass']
        if self.conn.add(target_dn, object_class, attributes):
            return True
        return self.check_error()

    def copy_to_ou(self, source_dn: str, target_ou: str) -> bool:
        dn_name = self.userDN_name(source_dn)
        return self.copy(source_dn, f'cn={dn_name},{target_ou}')

    def move(self, source_dn: str, target_dn: str) -> bool:
        if not self.copy(source_dn, target_dn):
            return self.check_error()
        if self.del_dn(source_dn):
            return True
        return self.check_error()

    def move_to_ou(self, source_dn: str, target_ou: str) -> bool:
        dn_name = self.userDN_name(source_dn)
        return self.move(source_dn, f'cn={dn_name},{target_ou}')

    def serach(self, base_dn: str, search_filter: str = '(cn=*)', search_scope: int = SUBTREE, attributes=None) -> list[str]:
        if not self.check_conn():
            return []
        if self.conn.search(base_dn, search_filter, search_scope, attributes=attributes):
            dn_list = []
            for entry in self.conn.entries:
                dn_list.append(entry.entry_dn)
            return dn_list
        self.check_error()
        return []

    def add_user(self, user: posixAccount | inetOrgPerson,need_hash_pw:bool=True,algorithm:str='SSHA') -> bool:
        class_list = ['top', 'inetOrgPerson']
        if isinstance(user,posixAccount):
            user.uidNumber = self.get_next_uid_number()
            class_list += ['posixAccount']
        elif isinstance(user,inetOrgPerson):
            pass
        else:
            raise ValueError(
                "user must be a posixAccount or inetOrgPerson type")
        if need_hash_pw and user.userPassword is not None:
            user.userPassword = self.hash(user.userPassword,algorithm)
        attributes = user.asdict()
        attributes = {k: v for k, v in attributes.items() if v is not None}
        user_dn = 'uid={uid},{LDAP_USER_BASE_DN}'.format(
            uid=user.uid, LDAP_USER_BASE_DN=self.ldap_config.USER_BASE_DN)
        return self.add(DN=user_dn, object_class=class_list, attributes=attributes)

    def del_uid(self, uid: str) -> bool:
        USER_DN = 'uid={uid},{LDAP_USER_BASE_DN}'.format(
            uid=uid, LDAP_USER_BASE_DN=self.ldap_config.USER_BASE_DN)
        return self.del_dn(USER_DN)

    def connect(self) -> bool:
        try:
            self.__server = self.__ldap_config.server()
            self.__conn = self.__ldap_config.connect()
            self.__conn_status = True
        except:
            self.__conn_status = False
        return self.conn_status

    def disconnect(self):
        if self.conn_status:
            self.conn.unbind()
            self.__conn_status = False
        return self.conn_status

    def check_conn(self) -> bool:
        if self.conn_status:
            return True
        if self.is_log:
            caller_name = inspect.stack()[1].function
            date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            msg = f'{date_time} {caller_name} connect_status_is_false'
            self.log(msg)
        return False

    def check_error(self) -> bool:
        # Always output False
        if self.is_log:
            caller_name = inspect.stack()[1].function
            self.conn.result['description']
            date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            msg = f'{date_time} {caller_name} {self.conn.result["description"]}'
            self.log(msg)
        return False

    def log(self, msg: str) -> None:
        print(msg)

    @classmethod
    def get_dn_name_list(cls, dn: str) -> list[str]:
        dn_list = dn.split(',')
        return dn_list

    @classmethod
    def userDN_name(cls, user_dn: str) -> str:
        dn_list = cls.get_dn_name_list(user_dn)
        return dn_list[0]

    @classmethod
    def hash(cls, value: str, algorithm: str = 'SSHA') -> str:
        if algorithm=='SSHA':
            return ldap_salted_sha1.hash(value)
        return hashed(algorithm, value)
