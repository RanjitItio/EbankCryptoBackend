from block_io import BlockIo


dogecoin = BlockIo('09d7-7b5c-a11d-a233','AEB8E42FA8E59592')
litcoin = BlockIo('ee6a-5cb6-4f85-3247','AEB8E42FA8E59592')
bitcoin = BlockIo('0d25-0de7-1052-e04a','AEB8E42FA8E59592')

# def Dogecoin_create_new_address(label=None):
    
#     response = dogecoin.get_new_address(label=label)
#     if response['status'] == 'success':
#         new_address = response['data']['address']
#         return new_address
#     else:
#         return None

# def litcoin_create_new_address(label=None):
    
#     response = litcoin.get_new_address(label=label)
#     if response['status'] == 'success':
#         new_address = response['data']['address']
#         return new_address
#     else:
#         return None
        

# def bitcoin_create_new_address(label=None):
    
#     response = bitcoin.get_new_address(label=label)
#     if response['status'] == 'success':
#         new_address = response['data']['address']
#         return new_address
#     else:
#         return None
    
    
class Dogecoin:
    def __init__(self, api_key, api_secret):
        self.client = BlockIo(api_key, api_secret)
    
    def create_new_address(self, label=None):
        response = self.client.get_new_address(label=label)
        if response['status'] == 'success':
            new_address = response['data']['address']
            return new_address
        else:
            return None
        
    def get_transection(self,address,type=None):
        response=self.client.get_transactions(address,type=type)
        if response['status'] == 'success':
            balance = response['data']['available_balance']
            return balance
        else:
            return None
        
    def get_balance(self, address):
        response = self.client.get_address_balance(address)
        if response['status'] == 'success':
            balance = response['data']['available_balance']
            return balance
        else:
            return None
        
    def send_transaction(self, from_address, to_address, amount, fee=None):
        response = self.client.send_from(from_address, to_address, amount, fee)
        if response['status'] == 'success':
            return True
        else:
            return False
    