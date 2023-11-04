from __future__ import annotations
from dataclasses import dataclass, asdict,fields
from ldap3 import Server, Connection, ALL, MODIFY_REPLACE, SUBTREE,MODIFY_DELETE,MODIFY_ADD
from typing import Any
import inspect
from datetime import datetime
from ldap3.utils.hashed import hashed
from passlib.hash import ldap_salted_sha1
from datetime import datetime
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
    POSIX_GROUP_RDN: str = None
    USER_FILTER: str = '(cn=*)'
    GROUP_FILTER: str = '(cn=*)'
    TLS:bool = False
    CERT_FILE:bool = None
    IS_AD:bool = False
    DOMAIN:str = None

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
        return self.get_dn_by_rdn(self.USER_BASE_RDN)

    @property
    def POSIX_GROUP_DN(self) -> str:
        if self.POSIX_GROUP_RDN is None or self.POSIX_GROUP_RDN.strip() == '':
            return self.GROUP_BASE_DN
        return self.get_dn_by_rdn(self.POSIX_GROUP_RDN)


    @property
    def GROUP_BASE_DN(self) -> str:
        return self.get_dn_by_rdn(self.GROUP_BASE_RDN)
    
    def get_dn_by_rdn(self, rdn: str) -> str:
        base_dn=self.BASE_DN
        if rdn is None or rdn.strip() == '':
            return base_dn
        return '{RDN},{BASE}'.format(RDN=rdn, BASE=base_dn)
    
    def get_user_dn(self, uid: str) -> str:
        return self.get_user_dn_ou(uid, self.USER_BASE_DN)

    def get_group_dn(self, cn: str) -> str:
        return self.get_group_dn_ou(cn, self.GROUP_BASE_DN)

    def get_posix_group_dn(self, cn: str) -> str:
        return self.get_group_dn_ou(cn, self.POSIX_GROUP_DN)

    def get_user_filter(self, uid: str) -> str:
        if self.USER_FILTER is None or self.USER_FILTER.strip() == '':
            return '(uid={UID})'.format(UID=uid)
        return '(&(uid={UID}){filter})'.format(UID=uid, filter=self.USER_FILTER)

    def get_group_filter(self, cn: str) -> str:
        if self.GROUP_FILTER is None or self.GROUP_FILTER.strip() == '':
            return '(cn={CN})'.format(CN=cn)
        return '(&(cn={CN}){filter})'.format(CN=cn, filter=self.GROUP_FILTER)



    @classmethod
    def get_user_dn_ou(cls,uid:str,ou_dn:str):
        return'uid={UID},{OU_DN}'.format(UID=uid,OU_DN=ou_dn)
    
    @classmethod
    def get_group_dn_ou(cls,cn:str,ou_dn:str):
        return'cn={CN},{OU_DN}'.format(CN=cn,OU_DN=ou_dn)
    
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
    gidNumber: int = 1000

class LDAP_OP:

    def __init__(self, ldap_config: LdapConfig = None, is_log: bool = False) -> None:
        self.__server: Server = None
        self.__conn: Connection = None
        self.__conn_status = False
        self.__last_error:str = None
        if ldap_config is not None and isinstance(LdapConfig, ldap_config):
            self.ldap_config = ldap_config
        else:
            self.__ldap_config = LdapConfig()
        self.is_log: bool = is_log
        self.__is_log_print: bool = False

    @property
    def ldap_config(self) -> LdapConfig:
        return self.__ldap_config
    @property
    def last_error(self) -> str:
        return self.__last_error
    @property
    def is_log_print(self) -> bool:
        return self.__is_log_print
    
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
            u0=1000
            for entry in self.conn.entries:
                uidNumber =int(entry['uidNumber'].value)
                if uidNumber<1000:
                    continue
                # print('uidNumber',uidNumber)
                if uidNumber-u0>1:
                    return u0+1
                u0=uidNumber
            return u0+1
        return 1000

    def add(self, DN: str, object_class: list[str], attributes: dict[str, Any]) -> bool:
        if not self.check_conn():
            return False
        if self.conn.add(DN, object_class, attributes):
            return True
        return self.check_error()

    def midify(self, dn: str, changes: dict[str, Any],mode=MODIFY_REPLACE) -> bool:
        if not self.check_conn():
            return False
        new_changes = {}
        for key, value in changes.items():
            new_changes[key] = [(mode, [value])]
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

    def copy(self, source_dn: str, target_dn: str,attr_exclude:list[str]=[]) -> bool:
        if not self.check_conn():
            return False
        if not self.conn.search(source_dn, '(objectClass=*)', attributes=['*']):
            return self.check_error()
        source_entry = self.conn.entries[0]
        # read source entry
        attributes = {}
        for attr in source_entry:
            if attr.key in attr_exclude:
                continue
            attributes[attr.key] = attr.value
        # attributes.pop('dn')
        object_class = attributes['objectClass']
        if self.conn.add(target_dn, object_class, attributes):
            return True
        return self.check_error()

    def copy_to_ou(self, source_dn: str, target_ou: str) -> bool:
        dn_name = self.userDN_name(source_dn)
        return self.copy(source_dn, f'cn={dn_name},{target_ou}')

    def move(self, source_dn: str, target_dn: str,attr_exclude:list[str]=[]) -> bool:
        if not self.copy(source_dn, target_dn,attr_exclude=attr_exclude):
            return self.check_error()
        if self.del_dn(source_dn):
            return True
        return self.check_error()

    def move_to_ou(self, source_dn: str, target_ou: str) -> bool:
        dn_name = self.userDN_name(source_dn)
        return self.move(source_dn, f'cn={dn_name},{target_ou}')

    def search(self, base_dn: str, search_filter: str = '(cn=*)', search_scope: int = SUBTREE, attributes=None) -> list[Any]:
        if not self.check_conn():
            return []
        if self.conn.search(base_dn, search_filter, search_scope, attributes=attributes):
            return self.conn.entries
        self.check_error()
        return []
    
    def check_dn(self,dn:str) -> bool:
        if not self.check_conn():
            return False
        if self.conn.search(dn, '(objectClass=*)', attributes=['*']):
            return True
        return False
    
    def search_user(self, uid: str,addition_attr:list[str]=[]) ->tuple[str, dict[str,Any]]:
        if not self.check_conn():
            return None
        search_filter=self.ldap_config.get_user_filter(uid)
        base_dn=self.ldap_config.USER_BASE_DN
        attributes = ['uid','givenName', 'sn', 'mail', 'telephoneNumber','memberOf']+addition_attr
        result= self.search(base_dn, search_filter, search_scope=SUBTREE, attributes=attributes)
        if len(result)==0:
            return '',{}
        entry=result[0]
        return entry.entry_dn,entry.entry_attributes_as_dict

    def add_user(self, user: posixAccount | inetOrgPerson,groups:list[str]=None,group_is_dn:bool=False,need_hash_pw:bool=True,algorithm:str='SSHA') -> bool:
        class_list = ['top', 'inetOrgPerson']
        if isinstance(user,posixAccount):
            user.uidNumber = self.get_next_uid_number()
            if user.uidNumber<0:
                return False
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
        user_dn = self.ldap_config.get_user_dn(user.uid)
        if self.is_log:
            print(f'attributes: {attributes}')
            print(f'class_list: {class_list}')
            print(f'user_info: {user}')
        if self.add(DN=user_dn, object_class=class_list, attributes=attributes):
            if groups is not None:
                self.add_user_to_groups(uid=user.uid,group_name=groups,group_is_dn=group_is_dn)
            return True
        return False


    def del_uid(self, uid: str) -> bool:
        USER_DN = self.ldap_config.get_user_dn(uid)
        return self.del_dn(USER_DN)

    def del_uid_tmp(self, uid: str,tmp_user_ou:str='') -> bool:
        tmp_ou_dn=self.ldap_config.get_dn_by_rdn(tmp_user_ou)
        if not self.check_conn() or not self.check_dn(tmp_ou_dn):
            return False
        user_dn=self.ldap_config.get_user_dn(uid)
        current_time=datetime.now().strftime('%Y%m%d%H%M%S%f')[:-4]
        tmp_user_dn = 'uid={uid}_{time},{ou}'.format(uid=uid,time=current_time,ou=tmp_ou_dn)
        return self.move(user_dn, tmp_user_dn,attr_exclude=['uid'])
    
    def create_group(self,name:str,objectClass:str='groupOfUniqueNames',members:list[str]=None,is_dn:bool=False,description:str=None,attr=None)->bool:
        group_dn=name
        if not is_dn:
            if objectClass=='posixGroup':
                group_dn=self.ldap_config.get_posix_group_dn(name)
            else:
                group_dn=self.ldap_config.get_group_dn(name)
                try:
                    members=[self.ldap_config.get_user_dn(uid) for uid in members]
                except:
                    members=None
        if self.check_dn(group_dn):
            return True
        attributes={}
        member_attr=self.get_attr_name_by_objectClass(objectClass=objectClass)
        if member_attr is not None and member_attr.strip()!='' and isinstance(members,list) and len(members)>0:
            attributes[member_attr]=members
        objectClass=['top',objectClass]
        if description is not None:
            attributes['description']=description
        if isinstance(attr,dict):
            for key,value in attr.items():
                if value is not None and key not in attributes:
                    attributes[key]=value
        return self.add(group_dn,object_class=objectClass,attributes=attributes)
    
    def create_posix_group(self,name:str,gidNumber:int,members:list[str]=None,is_dn:bool=False,description:str=None,attr=None)->bool:
        attributes={'gidNumber':gidNumber}
        if isinstance(attr,dict):
            for key,value in attr.items():
                if value is not None and key not in attributes:
                    attributes[key]=value
        return self.create_group(name=name,objectClass='posixGroup',members=members,is_dn=is_dn,description=description,attr=attributes)
    
    def modify_passwd(self, uid: str, new_passwd: str, algorithm: str = 'SSHA') -> bool:
        USER_DN = self.ldap_config.get_user_dn(uid)
        return self.midify(USER_DN, {'userPassword': self.hash(new_passwd,algorithm)})
    
    def bind_user_by_uid(self,uid:str,password:str)->bool:
        user_dn = self.ldap_config.get_user_dn(uid)
        return self.bind_user(user_dn,password)

    def bind_user(self,user_dn:str,password:str)->bool:
        if not self.check_conn():
            return False
        try:
            self.conn.bind(user_dn,password)
            self.conn.unbind()
            return True
        except:
            return False

    def get_member_attr_from_group(self,group_name:str,is_dn:bool=False)->str:
        if not self.check_conn():
            return []
        group_dn=group_name
        if not is_dn:
            group_dn=self.ldap_config.get_group_dn(group_dn)
        attr_name='objectClass'
        results= self.search(group_dn, '(objectClass=*)', attributes=[attr_name])
        if len(results)==0:
            return ''
        entry=results[0]
        class_names=entry.entry_attributes_as_dict[attr_name]
        return self.get_attr_name_by_objectClass(class_names)


    def add_user_to_group(self, uid: str, group_name:str,group_is_dn:bool=False,is_posix:bool=False) -> bool:
        if not self.check_conn():
            return False
        group_dn=group_name
        if not is_posix:
            if not group_is_dn:
                group_dn = self.ldap_config.get_group_dn(group_dn)
            member_attr_name=self.get_member_attr_from_group(group_dn,is_dn=True)
            if member_attr_name=='':
                return False
            user_dn = self.ldap_config.get_user_dn(uid)
        else:
            member_attr_name='memberUid'
            user_dn = uid
            if not group_is_dn:
                group_dn = self.ldap_config.get_posix_group_dn(group_dn)      
        if self.conn.modify(group_dn, {member_attr_name: [(MODIFY_ADD, [user_dn])]}):
            return True
        return self.check_error()

    def add_user_to_groups(self, uid: str, group_names:list[str],group_is_dn:bool=False,ignore_error:bool=True) -> bool:
        if not self.check_conn():
            return False
        for group_name in group_names:
            if not self.add_user_to_group(uid, group_name,group_is_dn=group_is_dn) and not ignore_error:
                return False
        return True



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
        self.__last_error = self.conn.result['description']
        if self.is_log:
            caller_name = inspect.stack()[1].function
            date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            msg = f'{date_time} {caller_name} {self.last_error}'
            self.log(msg)
        return False

    def log(self, msg: str) -> None:
        # if not self.is_log_print:
        print(msg)
            # self.is_log_print = True

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

    @classmethod
    def get_attr_name_by_objectClass(cls,objectClass:str|list[str])->str:
        if isinstance(objectClass,str):
            objectClass=[objectClass]
        elif isinstance(objectClass,list):
            pass
        else:
            return ''
        if 'groupOfNames' in objectClass:
            return 'member'
        elif 'groupOfUniqueNames' in objectClass:
            return 'uniqueMember'
        elif 'posixGroup' in objectClass:
            return 'memberUid'
        else:
            return ''