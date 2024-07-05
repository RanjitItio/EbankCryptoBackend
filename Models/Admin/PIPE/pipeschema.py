from dataclasses import dataclass, field
from typing import Optional



@dataclass
class AdminPipeCreateSchema:
    pipe_name: str
    status: str
    connect_mode: str
    prod_url: str
    test_url: str
    status_url: str
    process_mod: str
    process_cur: int

    #Processing Credentials
    headers: str
    body: str
    query: Optional[str]            = field(default=None) 
    auth_keys: Optional[str]        = field(default=None)

    type: Optional[int]             = field(default=None)
    settlement_prd: Optional[str]   = field(default='')
    refund_url: Optional[str]       = field(default='')
    refund_pol: Optional[str]       = field(default=None)
    auto_refnd: Optional[bool]      = field(default=False)
    white_ip:Optional[str]          = field(default='')
    webhook_url: Optional[str]      = field(default='')
    white_domain: Optional[str]     = field(default='')

    active_cntry: Optional[str]     = field(default=None)
    block_cntry: Optional[str]      = field(default=None)

    redirect_msg: Optional[str]     = field(default='')
    chkout_lable: Optional[str]     = field(default='')
    chkout_sub_lable: Optional[str] = field(default='')
    cmnt: Optional[str]             = field(default='')

    #Bank
    bnk_max_fail_trans_alwd: Optional[int] = field(default=0)
    bnk_dwn_period: Optional[str]          = field(default='')   
    bnk_sucs_resp: Optional[str]           = field(default='') 
    bnk_fl_resp: Optional[str]             = field(default='') 
    bnk_pndng_res: Optional[str]           = field(default='') 
    bnk_stus_path: Optional[str]           = field(default='')

    #Bank
    bnk_min_trans_lmt: Optional[int]   = field(default=0)
    bnk_max_trans_lmt: Optional[int]   = field(default=0)
    bnk_scrub_period: Optional[str]    = field(default='')
    bnk_trxn_cnt: Optional[int]        = field(default=0)
    bnk_min_sucs_cnt: Optional[int]    = field(default=0)
    bnk_min_fl_count: Optional[int]    = field(default=0)



@dataclass
class AdminPipeUpdateSchema:
    pipe_id: int
    pipe_name: str
    status: str
    connect_mode: str
    prod_url: str
    test_url: str
    status_url: str
    process_mod: str
    process_cur: int

    #Processing Credentials
    headers: str
    body: Optional[str]             = field(default=None) 
    query: Optional[str]            = field(default=None) 
    auth_keys: Optional[str]        = field(default=None)

    types: Optional[str]            = field(default=None)
    settlement_prd: Optional[str]   = field(default='')
    refund_url: Optional[str]       = field(default='')
    refund_pol: Optional[str]       = field(default=None)
    auto_refnd: Optional[bool]      = field(default=False)
    white_ip:Optional[str]          = field(default='')
    webhook_url: Optional[str]      = field(default='')
    white_domain: Optional[str]     = field(default='')

    active_cntry: Optional[str]     = field(default=None)
    block_cntry: Optional[str]      = field(default=None)

    redirect_msg: Optional[str]     = field(default='')
    chkout_lable: Optional[str]     = field(default='')
    chkout_sub_lable: Optional[str] = field(default='')
    cmnt: Optional[str]             = field(default='')

    #Bank
    bnk_max_fail_trans_alwd: Optional[int] = field(default=0)
    bnk_dwn_period: Optional[str]          = field(default='')   
    bnk_sucs_resp: Optional[str]           = field(default='') 
    bnk_fl_resp: Optional[str]             = field(default='') 
    bnk_pndng_res: Optional[str]           = field(default='') 
    bnk_stus_path: Optional[str]           = field(default='')

    #Bank
    bnk_min_trans_lmt: Optional[int]   = field(default=0)
    bnk_max_trans_lmt: Optional[int]   = field(default=0)
    bnk_scrub_period: Optional[str]    = field(default='')
    bnk_trxn_cnt: Optional[int]        = field(default=0)
    bnk_min_sucs_cnt: Optional[int]    = field(default=0)
    bnk_min_fl_count: Optional[int]    = field(default=0)



@dataclass
class AdminPipeConnectionModeCreateSchema:
    name: str

@dataclass
class AdminPipeConnectionModeUpdateSchema:
    connection_id: int
    name: str


@dataclass
class AdminCountryCreateSchema:
    name: str

@dataclass
class AdminCountryUpdateSchema:
    country_id: int
    name: str



@dataclass
class AdminPipeTypeCreateSchema:
    name: str


@dataclass
class AdminPipeTypeUpdateSchema:
    pipe_type_id: int
    name: str



# Merchant pipe assign schema
@dataclass
class AdminMerchantPipeAssignSchema:
    merchant_id: int
    pipe_id: int
    fee: float
    status: bool


# Mercant pipeupdate schema
@dataclass
class AdminMerchantPipeUdateSchema:
    merchant_pipe_id: int
    merchant_id: int
    pipe_id: int
    fee: float
    status: bool


